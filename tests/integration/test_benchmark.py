"""Test benchmark observations with deterministic synthetic responses."""

from pathlib import Path

from rag_security.backend import GenerationSettings, StaticTestBackend
from rag_security.benchmark import evaluate_case, run_benchmark
from rag_security.cases import CASES
from rag_security.corpus import load_corpus

CORPUS = Path(__file__).resolve().parents[2] / "data/synthetic/documents.json"


def test_variants_expose_different_contexts():
    documents = load_corpus(CORPUS)
    case = next(case for case in CASES if case.case_id == "cross_principal")
    backend = StaticTestBackend('{"answer": "Unknown", "sources": []}')

    protected = evaluate_case(
        documents,
        case=case,
        variant="protected",
        backend=backend,
        settings=GenerationSettings(),
    )
    vulnerable = evaluate_case(
        documents,
        case=case,
        variant="vulnerable_lab",
        backend=backend,
        settings=GenerationSettings(),
    )
    assert protected["forbidden_context_ids"] == []
    assert vulnerable["forbidden_context_ids"] == ["bob-private"]


def test_raw_canary_is_observed_even_with_invalid_citation():
    case = next(case for case in CASES if case.case_id == "cross_principal")
    record = evaluate_case(
        load_corpus(CORPUS),
        case=case,
        variant="protected",
        backend=StaticTestBackend(
            '{"answer": "BOB_PRIVATE_CANARY_7319", "sources": ["missing"]}'
        ),
        settings=GenerationSettings(),
    )
    assert record["forbidden_canary_in_raw"] is True
    assert record["response_error"] == "invalid_model_response"
    assert record["validated_answer"] is None


def test_generation_failure_is_not_a_successful_defense():
    class FailingBackend:
        def generate(self, messages, *, settings):
            raise OSError("Synthetic transport failure")

    record = evaluate_case(
        load_corpus(CORPUS),
        case=CASES[0],
        variant="protected",
        backend=FailingBackend(),
        settings=GenerationSettings(),
    )
    assert record["generation_status"] == "error"
    assert record["injection_canary_in_raw"] is None


def test_benchmark_keeps_manual_review_pending():
    report = run_benchmark(
        load_corpus(CORPUS),
        backend_factory=lambda seed: StaticTestBackend(
            '{"answer": "Unknown", "sources": []}'
        ),
        seeds=(42,),
    )
    assert len(report["records"]) == 2 * len(CASES)
    assert all(
        record["manual_review"]["grounded_answer"] is None
        for record in report["records"]
    )
