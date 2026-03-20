from types import SimpleNamespace

from app.core.config import Settings
from app.providers.anthropic_provider import AnthropicProvider


class FakeBlock(SimpleNamespace):
    pass


class FakeResponse(SimpleNamespace):
    def model_dump(self):
        return {"ok": True}


def test_anthropic_normalization_extracts_text_tools_and_usage():
    provider = AnthropicProvider(Settings(anthropic_api_key="test-key"))
    response = FakeResponse(
        content=[
            FakeBlock(type="text", text="Hello "),
            FakeBlock(type="tool_use", id="call_1", name="search_documents", input={"query": "x"}),
            FakeBlock(type="text", text="world"),
        ],
        usage=SimpleNamespace(input_tokens=12, output_tokens=34),
        stop_reason="end_turn",
        model="claude-test",
    )

    normalized = provider._normalize_response(response)
    assert normalized.message.content == "Hello world"
    assert len(normalized.tool_calls) == 1
    assert normalized.tool_calls[0].name == "search_documents"
    assert normalized.usage.input_tokens == 12
    assert normalized.usage.output_tokens == 34
