"""Filter documents before retrieval or context construction."""

from rag_security.models import Document, Principal

MAX_CORPUS_DOCUMENTS = 1_000


def authorized_documents(
    documents,
    *,
    principal: Principal,
) -> tuple[Document, ...]:
    """Return only explicitly authorized documents from a validated corpus."""
    if not isinstance(principal, Principal):
        raise ValueError("A validated principal is required.")

    seen = set()
    authorized = []

    for index, document in enumerate(documents):
        if index >= MAX_CORPUS_DOCUMENTS:
            raise ValueError("Corpus exceeds the document count limit.")
        if not isinstance(document, Document):
            raise ValueError("Corpus requires validated documents.")
        if document.document_id in seen:
            raise ValueError("Duplicate document identifier.")
        seen.add(document.document_id)

        if principal.principal_id in document.allowed_principals:
            authorized.append(document)

    return tuple(authorized)
