"""Exercise orchestration with a test backend, not model security claims."""

import json
from pathlib import Path

import pytest

from rag_security.assistant import answer_question
from rag_security.backend import GenerationSettings, StaticTestBackend
from rag_security.corpus import load_corpus
from rag_security.models import Principal
from rag_security.prompting import parse_answer

CORPUS = Path(__file__).resolve().parents[2] / "data/synthetic/documents.json"


def test_valid_response_retains_actual_context():
    run = answer_question(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Atlas review schedule",
        backend=StaticTestBackend(
            '{"answer": "Tuesday at 10:00.", "sources": ["alice-project"]}'
        ),
    )
    assert run.response_error is None
    assert run.answer.sources == ("alice-project",)
    assert "bob-private" not in run.context.document_ids
    assert [message.role for message in run.messages] == ["system", "user"]
    payload = json.loads(run.messages[1].content)
    assert payload["question"] == "Atlas review schedule"


def test_forbidden_citation_is_rejected_but_raw_output_retained():
    raw = '{"answer": "BOB_PRIVATE_CANARY_7319", "sources": ["bob-private"]}'
    run = answer_question(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Boreal access code",
        backend=StaticTestBackend(raw),
    )
    assert run.context.document_ids == ()
    assert run.answer is None
    assert run.response_error == "invalid_model_response"
    assert run.raw_response == raw


def test_valid_citation_does_not_filter_injection_canary():
    run = answer_question(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Atlas meeting",
        backend=StaticTestBackend(
            '{"answer": "INJECTION_CANARY_8426", "sources": ["alice-injected"]}'
        ),
    )
    assert run.response_error is None
    assert run.answer.answer == "INJECTION_CANARY_8426"
    # A structurally valid response can still follow a malicious instruction.


@pytest.mark.parametrize(
    "raw",
    [
        "not JSON",
        '{"answer": "x", "answer": "y", "sources": []}',
        '{"answer": "", "sources": []}',
        '{"answer": "x", "sources": ["missing"]}',
        '{"answer": "x", "sources": ["doc", "doc"]}',
        '{"answer": "x", "sources": [], "extra": true}',
        '{"answer": "x", "sources": null}',
    ],
)
def test_invalid_answers_are_rejected(raw):
    with pytest.raises(ValueError):
        parse_answer(raw, supplied_document_ids=("doc",))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_new_tokens", 0),
        ("max_new_tokens", 513),
        ("max_new_tokens", True),
        ("timeout_seconds", 0),
        ("timeout_seconds", 301),
    ],
)
def test_invalid_generation_settings_are_rejected(field, value):
    with pytest.raises(ValueError):
        GenerationSettings(**{field: value})
