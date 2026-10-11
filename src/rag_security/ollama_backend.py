"""Bounded adapter for the local Ollama chat endpoint."""

import json
import urllib.request
from dataclasses import asdict

from rag_security.backend import GenerationSettings
from rag_security.prompting import MAX_RESPONSE_CHARACTERS, ModelMessage

ENDPOINT = "http://127.0.0.1:11434/api/chat"
MAX_HTTP_RESPONSE_BYTES = 100_000
MAX_MESSAGES_CHARACTERS = 16_000


class OllamaBackend:
    """Run the selected local model without proxies or external tools."""

    def __init__(self, *, model: str = "qwen2.5:0.5b", seed: int = 42):
        if not isinstance(model, str) or model != "qwen2.5:0.5b":
            raise ValueError("This adapter supports the reviewed local model.")
        if type(seed) is not int or not 0 <= seed < 2**32:
            raise ValueError("Invalid generation seed.")
        self.model = model
        self.seed = seed
        self.last_metadata = None
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def generate(
        self,
        messages: tuple[ModelMessage, ...],
        *,
        settings: GenerationSettings,
    ) -> str:
        self.last_metadata = None
        if not isinstance(settings, GenerationSettings):
            raise ValueError("Validated generation settings are required.")
        if (
            not isinstance(messages, tuple)
            or not 1 <= len(messages) <= 4
            or any(
                not isinstance(message, ModelMessage)
                or message.role not in {"system", "user"}
                or not isinstance(message.content, str)
                for message in messages
            )
        ):
            raise ValueError("Invalid model messages.")
        if sum(len(message.content) for message in messages) > (
            MAX_MESSAGES_CHARACTERS
        ):
            raise ValueError("Messages exceed the character limit.")

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [asdict(message) for message in messages],
            "options": {
                "temperature": 0,
                "seed": self.seed,
                "num_predict": settings.max_new_tokens,
                "num_ctx": 4096,
            },
        }
        request = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload, allow_nan=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self._opener.open(request, timeout=settings.timeout_seconds) as response:
            raw = response.read(MAX_HTTP_RESPONSE_BYTES + 1)

        if len(raw) > MAX_HTTP_RESPONSE_BYTES:
            raise ValueError("HTTP response exceeds the byte limit.")
        result = json.loads(raw)
        if not isinstance(result, dict) or result.get("done") is not True:
            raise ValueError("Incomplete model response.")
        if result.get("model") != self.model:
            raise ValueError("Unexpected response model.")
        if result.get("done_reason") != "stop":
            raise ValueError("Generation did not stop normally.")

        message = result.get("message")
        if (
            not isinstance(message, dict)
            or message.get("role") != "assistant"
            or not isinstance(message.get("content"), str)
        ):
            raise ValueError("Invalid assistant message.")
        content = message["content"]
        if not content.strip() or len(content) > MAX_RESPONSE_CHARACTERS:
            raise ValueError("Model output exceeds application bounds.")

        self.last_metadata = {
            key: result.get(key)
            for key in (
                "model",
                "done_reason",
                "total_duration",
                "load_duration",
                "prompt_eval_count",
                "eval_count",
            )
        }
        return content
