"""Offline analysis of previously recorded synthetic RAG experiments."""

import argparse
import json
import sys
from pathlib import Path

from rag_security.observations import summarize_records

MAX_REPORT_BYTES = 5_000_000


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON value.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        with args.report.open("rb") as source:
            raw = source.read(MAX_REPORT_BYTES + 1)
        if len(raw) > MAX_REPORT_BYTES:
            raise ValueError("Report exceeds the byte limit.")
        report = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if (
            not isinstance(report, dict)
            or type(report.get("schema_version")) is not int
            or report["schema_version"] != 1
        ):
            raise ValueError("Unsupported report schema.")

        summary = summarize_records(report.get("records"))
        output = {
            "schema_version": 1,
            "analysis_status": "complete",
            "measurement": "literal canaries and recorded context exposure",
            "summary": summary,
            "manual_quality_review": "not assessed by this command",
        }
        content = json.dumps(output, indent=2, allow_nan=False)
        print(content)

    except (OSError, ValueError) as exc:
        print(
            f"Report analysis failed ({type(exc).__name__}).",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
