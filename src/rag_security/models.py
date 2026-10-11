"""Validated immutable objects for the local RAG security harness."""

import re
from dataclasses import dataclass

MAX_DOCUMENT_CHARACTERS = 20_000
MAX_QUERY_CHARACTERS = 2_000
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def validate_identifier(value: str) -> None:
    if not isinstance(value, str) or not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError("Identifier must use 1-64 ASCII letters, digits, _ or -.")


@dataclass(frozen=True)
class Principal:
    """A synthetic identity supplied by trusted harness configuration."""

    principal_id: str

    def __post_init__(self):
        validate_identifier(self.principal_id)


@dataclass(frozen=True)
class Document:
    """Untrusted document content with separately supplied access metadata."""

    document_id: str
    title: str
    content: str
    allowed_principals: frozenset[str]

    def __post_init__(self):
        validate_identifier(self.document_id)
        if (
            not isinstance(self.title, str)
            or not self.title.strip()
            or len(self.title) > 200
        ):
            raise ValueError("Document title must contain 1-200 characters.")
        if (
            not isinstance(self.content, str)
            or not self.content.strip()
            or len(self.content) > MAX_DOCUMENT_CHARACTERS
        ):
            raise ValueError("Document content is empty or exceeds the limit.")
        if type(self.allowed_principals) is not frozenset:
            raise ValueError("Allowed principals must be an immutable set.")
        for principal_id in self.allowed_principals:
            validate_identifier(principal_id)


def validate_query(query: str) -> None:
    if (
        not isinstance(query, str)
        or not query.strip()
        or len(query) > MAX_QUERY_CHARACTERS
    ):
        raise ValueError("Query is empty or exceeds the character limit.")
