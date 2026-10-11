"""Read bounded synthetic document corpora with strict metadata validation."""

import json
from pathlib import Path

from rag_security.authorization import MAX_CORPUS_DOCUMENTS
from rag_security.models import Document

MAX_CORPUS_BYTES = 5_000_000


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-finite JSON constant.")


def load_corpus(path: Path) -> tuple[Document, ...]:
    with Path(path).open("rb") as source:
        raw = source.read(MAX_CORPUS_BYTES + 1)
    if len(raw) > MAX_CORPUS_BYTES:
        raise ValueError("Corpus exceeds the byte limit.")

    data = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(data, dict) or set(data) != {"schema_version", "documents"}:
        raise ValueError("Invalid corpus structure.")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported corpus schema.")

    entries = data["documents"]
    if (
        not isinstance(entries, list)
        or not entries
        or len(entries) > MAX_CORPUS_DOCUMENTS
    ):
        raise ValueError("Invalid document collection.")

    documents = []
    seen = set()
    expected = {"document_id", "title", "content", "allowed_principals"}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != expected:
            raise ValueError("Invalid document fields.")
        readers = entry["allowed_principals"]
        if not isinstance(readers, list) or any(
            not isinstance(reader, str) for reader in readers
        ):
            raise ValueError("Invalid allowed principal list.")
        if len(set(readers)) != len(readers):
            raise ValueError("Duplicate allowed principal.")

        document = Document(
            document_id=entry["document_id"],
            title=entry["title"],
            content=entry["content"],
            allowed_principals=frozenset(readers),
        )
        if document.document_id in seen:
            raise ValueError("Duplicate document identifier.")
        seen.add(document.document_id)
        documents.append(document)

    return tuple(documents)
