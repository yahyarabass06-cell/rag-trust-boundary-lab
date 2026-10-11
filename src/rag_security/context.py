"""Assemble bounded context only through authorization-first retrieval."""

import json
from dataclasses import dataclass

from rag_security.models import Principal
from rag_security.retrieval import retrieve_documents

MAX_CONTEXT_CHARACTERS = 8_000


@dataclass(frozen=True)
class RetrievalContext:
    payload: str
    document_ids: tuple[str, ...]
    omitted_document_ids: tuple[str, ...]


def build_context(
    documents,
    *,
    principal: Principal,
    query: str,
    top_k: int = 3,
    max_characters: int = MAX_CONTEXT_CHARACTERS,
) -> RetrievalContext:
    if (
        type(max_characters) is not int
        or not 100 <= max_characters <= MAX_CONTEXT_CHARACTERS
    ):
        raise ValueError("Context budget must be between 100 and 8000.")

    matches = retrieve_documents(
        documents, principal=principal, query=query, top_k=top_k
    )
    included = []
    omitted = []
    payload = "[]"

    for match in matches:
        document = match.document
        entry = {
            "document_id": document.document_id,
            "title": document.title,
            "content": document.content,
        }
        candidate = json.dumps(included + [entry], ensure_ascii=False)
        if len(candidate) <= max_characters:
            included.append(entry)
            payload = candidate
        else:
            omitted.append(document.document_id)

    return RetrievalContext(
        payload=payload,
        document_ids=tuple(entry["document_id"] for entry in included),
        omitted_document_ids=tuple(omitted),
    )
