"""Model adapter contract and a deterministic software-test backend."""

from dataclasses import dataclass
from typing import Protocol

from rag_security.prompting import ModelMessage


@dataclass(frozen=True)
class GenerationSettings:
    max_new_tokens: int = 256
    timeout_seconds: int = 120

    def __post_init__(self):
        if type(self.max_new_tokens) is not int or not 1 <= self.max_new_tokens <= 512:
            raise ValueError("Generation limit must be between 1 and 512.")
        if (
            type(self.timeout_seconds) is not int
            or not 1 <= self.timeout_seconds <= 300
        ):
            raise ValueError("Timeout must be between 1 and 300 seconds.")


class ModelBackend(Protocol):
    def generate(
        self,
        messages: tuple[ModelMessage, ...],
        *,
        settings: GenerationSettings,
    ) -> str:
        """Return raw model output under adapter-enforced resource limits."""
        ...


class StaticTestBackend:
    """Return a fixed response; this is not a language model."""

    def __init__(self, response: str):
        self.response = response

    def generate(
        self,
        messages: tuple[ModelMessage, ...],
        *,
        settings: GenerationSettings,
    ) -> str:
        if not isinstance(settings, GenerationSettings):
            raise ValueError("Validated generation settings are required.")
        if not messages or any(
            not isinstance(message, ModelMessage) for message in messages
        ):
            raise ValueError("Validated messages are required.")
        return self.response
