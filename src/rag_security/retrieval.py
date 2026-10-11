"""Authorization-first lexical retrieval with deterministic ranking."""

import re
from dataclasses import dataclass

from rag_security.authorization import authorized_documents
from rag_security.models import Document, Principal, validate_query


@dataclass(frozen=True)
class RetrievedDocument:
    document: Document
    score: float


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold()))


def retrieve_documents(
    documents,
    *,
    principal: Principal,
    query: str,
    top_k: int = 3,
) -> tuple[RetrievedDocument, ...]:
    validate_query(query)
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10.")

    permitted = authorized_documents(documents, principal=principal)
    query_tokens = _tokens(query)
    if not query_tokens:
        raise ValueError("Query must contain searchable words.")

    matches = []
    for document in permitted:
        document_tokens = _tokens(document.title + " " + document.content)
        overlap = query_tokens & document_tokens
        if overlap:
            matches.append(
                RetrievedDocument(
                    document=document,
                    score=len(overlap) / len(query_tokens),
                )
            )

    matches.sort(key=lambda match: (-match.score, match.document.document_id))
    return tuple(matches[:top_k])
