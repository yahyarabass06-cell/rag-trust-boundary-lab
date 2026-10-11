"""Verify offline report CLI outcomes."""

import json
import subprocess
import sys


def run_cli(path):
    return subprocess.run(
        [sys.executable, "-m", "rag_security.cli", "--report", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_report_is_summarized(tmp_path):
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "records": [
                    {
                        "variant": "protected",
                        "case_id": "example",
                        "seed": 42,
                        "context": {"document_ids": []},
                        "forbidden_context_ids": [],
                        "generation_status": "complete",
                        "raw_response": '{"answer": "Unknown", "sources": []}',
                        "response_error": None,
                    }
                ],
            }
        )
    )
    result = run_cli(path)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["summary"]["protected"]["completed"] == 1


def test_missing_report_produces_no_success_json(tmp_path):
    result = run_cli(tmp_path / "missing.json")
    assert result.returncode == 2
    assert result.stdout == ""


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "report.json"
    path.write_text('{"schema_version": 1, "schema_version": 1}')
    result = run_cli(path)
    assert result.returncode == 2
    assert result.stdout == ""
