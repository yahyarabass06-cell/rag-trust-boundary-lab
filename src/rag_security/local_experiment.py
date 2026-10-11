"""Run paired synthetic RAG experiments with local model provenance."""

import argparse
import hashlib
import json
import platform
import sys
import urllib.request
from pathlib import Path

from rag_security.benchmark import run_benchmark
from rag_security.corpus import MAX_CORPUS_BYTES, load_corpus
from rag_security.exporting import write_new_report
from rag_security.observations import summarize_records
from rag_security.ollama_backend import OllamaBackend

MODEL = "qwen2.5:0.5b"


def local_metadata(endpoint: str) -> dict:
    if endpoint not in {"/api/tags", "/api/version"}:
        raise ValueError("Unsupported metadata endpoint.")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open("http://127.0.0.1:11434" + endpoint, timeout=10) as response:
        raw = response.read(1_000_001)
    if len(raw) > 1_000_000:
        raise ValueError("Metadata response exceeds the byte limit.")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("Invalid metadata response.")
    return data


def selected_identity() -> dict:
    models = local_metadata("/api/tags").get("models")
    if not isinstance(models, list):
        raise ValueError("Invalid model inventory.")
    matches = [
        model
        for model in models
        if isinstance(model, dict) and model.get("name") == MODEL
    ]
    if len(matches) != 1:
        raise ValueError("Model identity is missing or ambiguous.")
    identity = matches[0]
    digest = identity.get("digest")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError("A complete SHA-256 model digest is required.")
    return identity


def execute(corpus_path: Path, *, seeds: tuple[int, ...]) -> dict:
    with corpus_path.open("rb") as source:
        raw = source.read(MAX_CORPUS_BYTES + 1)
    if len(raw) > MAX_CORPUS_BYTES:
        raise ValueError("Corpus exceeds the byte limit.")
    documents = load_corpus(corpus_path)
    if hashlib.sha256(corpus_path.read_bytes()).digest() != (
        hashlib.sha256(raw).digest()
    ):
        raise ValueError("Corpus changed during loading.")

    identity_before = selected_identity()
    version_before = local_metadata("/api/version")
    report = run_benchmark(
        documents,
        backend_factory=lambda seed: OllamaBackend(seed=seed),
        seeds=seeds,
    )
    identity_after = selected_identity()
    version_after = local_metadata("/api/version")

    report["provenance"] = {
        "model_tag": MODEL,
        "model_before": identity_before,
        "model_after": identity_after,
        "ollama_before": version_before,
        "ollama_after": version_after,
        "environment_stable": (
            identity_before["digest"] == identity_after["digest"]
            and version_before == version_after
        ),
        "corpus_sha256": hashlib.sha256(raw).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "generation_options": {
            "temperature": 0,
            "num_ctx": 4096,
            "format": "json",
        },
    }
    # Normalize tuples to the JSON report representation before summarizing.
    report = json.loads(json.dumps(report, allow_nan=False))
    report["summary"] = summarize_records(report["records"])
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    args = parser.parse_args(argv)

    try:
        seeds = tuple(args.seeds)
        if (
            not 1 <= len(seeds) <= 5
            or len(set(seeds)) != len(seeds)
            or any(not 0 <= seed < 2**32 for seed in seeds)
        ):
            raise ValueError("Use one to five distinct valid seeds.")
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("Output already exists.")
        if not args.output.parent.is_dir():
            raise ValueError("Output directory must already exist.")

        print("Running local model experiment...", file=sys.stderr)
        report = execute(args.corpus, seeds=seeds)
        content = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
        write_new_report(args.output, content + "\n")
        print(f"Report saved: {args.output}", file=sys.stderr)

        complete = all(
            record["generation_status"] == "complete" for record in report["records"]
        )
        if not complete or not report["provenance"]["environment_stable"]:
            print("Experiment incomplete or environment changed.", file=sys.stderr)
            return 2
        return 0

    except (OSError, ValueError) as exc:
        print(f"Experiment failed ({type(exc).__name__}).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
