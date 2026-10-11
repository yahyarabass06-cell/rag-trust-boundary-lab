"""Verify isolation across a small synthetic multi-principal corpus."""

from rag_security.authorization import authorized_documents
from rag_security.models import Document, Principal


def test_principals_receive_only_explicitly_authorized_content():
    corpus = [
        Document(
            document_id="shared",
            title="Shared procedures",
            content="Shared synthetic procedure.",
            allowed_principals=frozenset({"alice", "bob"}),
        ),
        Document(
            document_id="alice-private",
            title="Alice private notes",
            content="ALICE_PRIVATE_CANARY",
            allowed_principals=frozenset({"alice"}),
        ),
        Document(
            document_id="bob-private",
            title="Bob private notes",
            content="BOB_PRIVATE_CANARY",
            allowed_principals=frozenset({"bob"}),
        ),
    ]

    alice_documents = authorized_documents(corpus, principal=Principal("alice"))
    bob_documents = authorized_documents(corpus, principal=Principal("bob"))

    assert {doc.document_id for doc in alice_documents} == {"shared", "alice-private"}
    assert {doc.document_id for doc in bob_documents} == {"shared", "bob-private"}
    assert "BOB_PRIVATE_CANARY" not in "\n".join(doc.content for doc in alice_documents)
    assert "ALICE_PRIVATE_CANARY" not in "\n".join(doc.content for doc in bob_documents)
