"""Verify experiment publication behavior without running a model."""

import json

from rag_security import local_experiment


def synthetic_report(*, complete=True):
    return {
        "provenance": {"environment_stable": True},
        "records": [{"generation_status": "complete" if complete else "error"}],
    }


def test_complete_experiment_is_exported(tmp_path, monkeypatch):
    monkeypatch.setattr(
        local_experiment,
        "execute",
        lambda *args, **kwargs: synthetic_report(),
    )
    path = tmp_path / "report.json"
    code = local_experiment.main(["--corpus", "synthetic.json", "--output", str(path)])
    assert code == 0
    assert json.loads(path.read_text())["provenance"]["environment_stable"]


def test_failed_generations_remain_in_saved_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        local_experiment,
        "execute",
        lambda *args, **kwargs: synthetic_report(complete=False),
    )
    path = tmp_path / "report.json"
    code = local_experiment.main(["--corpus", "synthetic.json", "--output", str(path)])
    assert code == 2
    assert json.loads(path.read_text())["records"][0]["generation_status"] == ("error")


def test_collision_is_rejected_before_model_execution(tmp_path, monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Model execution must not occur.")

    monkeypatch.setattr(local_experiment, "execute", unexpected_call)
    path = tmp_path / "report.json"
    path.write_text("original")
    assert (
        local_experiment.main(["--corpus", "synthetic.json", "--output", str(path)])
        == 2
    )
    assert path.read_text() == "original"


def test_invalid_seed_does_not_run_model(tmp_path, monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Model execution must not occur.")

    monkeypatch.setattr(local_experiment, "execute", unexpected_call)
    assert (
        local_experiment.main(
            [
                "--corpus",
                "synthetic.json",
                "--output",
                str(tmp_path / "report.json"),
                "--seeds",
                "-1",
            ]
        )
        == 2
    )
