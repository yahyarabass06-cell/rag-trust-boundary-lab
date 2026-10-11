"""Verify authorization before ranking and actual context isolation."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from rag_security.context import build_context
from rag_security.corpus import load_corpus
from rag_security.models import Principal
from rag_security.retrieval import retrieve_documents

CORPUS = Path(__file__).resolve().parents[2] / "data/synthetic/documents.json"


def test_private_document_never_enters_alice_context():
    context = build_context(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Boreal BOB_PRIVATE_CANARY_7319",
    )
    assert context.document_ids == ()
    assert json.loads(context.payload) == []
    assert "BOB_PRIVATE_CANARY_7319" not in context.payload


def test_bob_can_retrieve_own_document():
    matches = retrieve_documents(
        load_corpus(CORPUS),
        principal=Principal("bob"),
        query="Boreal access code",
    )
    assert matches[0].document.document_id == "bob-private"


def test_authorized_injection_is_still_untrusted_context():
    context = build_context(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Atlas meeting",
    )
    assert "alice-injected" in context.document_ids
    assert "INJECTION_CANARY_8426" in context.payload
    assert "bob-private" not in context.document_ids


def test_context_identifiers_match_actual_payload():
    context = build_context(
        load_corpus(CORPUS),
        principal=Principal("alice"),
        query="Atlas project",
    )
    assert (
        tuple(entry["document_id"] for entry in json.loads(context.payload))
        == context.document_ids
    )


def test_context_budget_omits_complete_document():
    document = load_corpus(CORPUS)[1]
    oversized = replace(document, content="Atlas " * 1000)
    context = build_context(
        [oversized],
        principal=Principal("alice"),
        query="Atlas",
        max_characters=100,
    )
    assert len(context.payload) <= 100
    assert context.document_ids == ()
    assert context.omitted_document_ids == ("alice-project",)


def test_ranking_ties_are_deterministic():
    document = load_corpus(CORPUS)[1]
    other = replace(document, document_id="a-first")
    matches = retrieve_documents(
        [document, other],
        principal=Principal("alice"),
        query="Atlas",
    )
    assert [match.document.document_id for match in matches] == [
        "a-first",
        "alice-project",
    ]


@pytest.mark.parametrize("top_k", [0, 11, True])
def test_invalid_retrieval_limit_is_rejected(top_k):
    with pytest.raises(ValueError):
        retrieve_documents(
            load_corpus(CORPUS),
            principal=Principal("alice"),
            query="Atlas",
            top_k=top_k,
        )


@pytest.mark.parametrize(
    "content",
    [
        '{"schema_version": 1, "schema_version": 1}',
        '{"schema_version": true, "documents": []}',
        '{"schema_version": 1, "documents": [], "extra": 1}',
        '{"schema_version": NaN, "documents": []}',
    ],
)
def test_invalid_corpus_is_rejected(tmp_path, content):
    path = tmp_path / "documents.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_corpus(path)
