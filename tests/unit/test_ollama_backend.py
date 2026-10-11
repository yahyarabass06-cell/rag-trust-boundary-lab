"""Test local adapter contracts with a simulated HTTP transport."""

import json

import pytest

from rag_security.backend import GenerationSettings
from rag_security.ollama_backend import ENDPOINT, OllamaBackend
from rag_security.prompting import ModelMessage


class FakeResponse:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.content[:limit]


class FakeOpener:
    def __init__(self, result):
        self.result = result
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        return FakeResponse(json.dumps(self.result).encode("utf-8"))


@pytest.fixture
def response():
    return {
        "model": "qwen2.5:0.5b",
        "done": True,
        "done_reason": "stop",
        "message": {
            "role": "assistant",
            "content": '{"answer": "Cedar", "sources": ["lab-note"]}',
        },
        "eval_count": 20,
    }


def test_request_is_local_bounded_and_without_tools(response):
    backend = OllamaBackend()
    transport = FakeOpener(response)
    backend._opener = transport

    output = backend.generate(
        (ModelMessage("user", "Synthetic question"),),
        settings=GenerationSettings(max_new_tokens=128, timeout_seconds=30),
    )

    assert output == response["message"]["content"]
    assert transport.request.full_url == ENDPOINT
    assert transport.timeout == 30
    payload = json.loads(transport.request.data)
    assert payload["stream"] is False
    assert payload["options"]["num_predict"] == 128
    assert payload["options"]["temperature"] == 0
    assert "tools" not in payload
    assert backend.last_metadata["eval_count"] == 20


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("done", False),
        ("done_reason", "length"),
        ("model", "unexpected-model"),
        ("message", {}),
    ],
)
def test_invalid_server_response_is_rejected(response, field, value):
    response[field] = value
    backend = OllamaBackend()
    backend._opener = FakeOpener(response)
    with pytest.raises(ValueError):
        backend.generate(
            (ModelMessage("user", "Question"),),
            settings=GenerationSettings(),
        )
    assert backend.last_metadata is None


def test_excessive_output_is_rejected(response):
    response["message"]["content"] = "x" * 4001
    backend = OllamaBackend()
    backend._opener = FakeOpener(response)
    with pytest.raises(ValueError, match="bounds"):
        backend.generate(
            (ModelMessage("user", "Question"),),
            settings=GenerationSettings(),
        )


def test_excessive_input_is_rejected():
    with pytest.raises(ValueError, match="character limit"):
        OllamaBackend().generate(
            (ModelMessage("user", "x" * 16001),),
            settings=GenerationSettings(),
        )
