"""Protected assistant orchestration with retained raw model output."""

from dataclasses import dataclass

from rag_security.backend import GenerationSettings, ModelBackend
from rag_security.context import RetrievalContext, build_context
from rag_security.models import Principal
from rag_security.prompting import (
    AssistantAnswer,
    ModelMessage,
    build_messages,
    parse_answer,
)


@dataclass(frozen=True)
class AssistantRun:
    context: RetrievalContext
    messages: tuple[ModelMessage, ...]
    raw_response: str
    answer: AssistantAnswer | None
    response_error: str | None


def answer_question(
    documents,
    *,
    principal: Principal,
    query: str,
    backend: ModelBackend,
    settings: GenerationSettings = GenerationSettings(),
) -> AssistantRun:
    context = build_context(documents, principal=principal, query=query)
    messages = build_messages(query=query, context=context)
    raw = backend.generate(messages, settings=settings)

    try:
        answer = parse_answer(raw, supplied_document_ids=context.document_ids)
        error = None
    except ValueError:
        answer = None
        error = "invalid_model_response"

    return AssistantRun(
        context=context,
        messages=messages,
        raw_response=raw,
        answer=answer,
        response_error=error,
    )
