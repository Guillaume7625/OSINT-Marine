from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from anthropic import NOT_GIVEN, AsyncAnthropic

from app.core.config import Settings
from app.providers.base import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    LLMProvider,
    ModelCapabilities,
    StreamEvent,
    ToolCall,
    ToolSpec,
    UsageMetadata,
)

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.anthropic_timeout_seconds,
        )

    def capabilities(self, model: str) -> ModelCapabilities:
        return ModelCapabilities(model=model, provider=self.name, supports_streaming=True, supports_tool_calling=True)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        anthropic_messages = self._to_anthropic_messages(request.messages)
        anthropic_tools = self._to_anthropic_tools(request.tools)

        response = await self.client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system=request.system_prompt if request.system_prompt else NOT_GIVEN,
            messages=anthropic_messages,
            tools=anthropic_tools if anthropic_tools else NOT_GIVEN,
        )
        return self._normalize_response(response)

    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        anthropic_messages = self._to_anthropic_messages(request.messages)
        anthropic_tools = self._to_anthropic_tools(request.tools)
        try:
            async with self.client.messages.stream(
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=request.system_prompt if request.system_prompt else NOT_GIVEN,
                messages=anthropic_messages,
                tools=anthropic_tools if anthropic_tools else NOT_GIVEN,
            ) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield StreamEvent(type="text_delta", delta=text)

                final_message = await stream.get_final_message()
                normalized = self._normalize_response(final_message)
                yield StreamEvent(type="usage", usage=normalized.usage)
                for tool_call in normalized.tool_calls:
                    yield StreamEvent(type="tool_call", tool_call=tool_call)
                yield StreamEvent(type="done", response=normalized)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Anthropic streaming error")
            yield StreamEvent(type="error", error=str(exc))

    def _to_anthropic_tools(self, tools: list[ToolSpec]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for tool in tools:
            payload.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )
        return payload

    def _to_anthropic_messages(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        payload: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                continue

            if msg.role == "tool":
                if not msg.tool_call_id:
                    logger.warning("Skipping tool message without tool_call_id")
                    continue
                payload.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content,
                            }
                        ],
                    }
                )
                continue

            if msg.role == "assistant" and msg.tool_calls:
                content: list[dict[str, Any]] = []
                if msg.content.strip():
                    content.append({"type": "text", "text": msg.content})
                for call in msg.tool_calls:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": call.id,
                            "name": call.name,
                            "input": call.arguments,
                        }
                    )
                payload.append({"role": "assistant", "content": content})
                continue

            payload.append(
                {
                    "role": "assistant" if msg.role == "assistant" else "user",
                    "content": msg.content,
                }
            )
        return payload

    def _normalize_response(self, response: Any) -> ChatResponse:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=block.input or {}))

        usage = UsageMetadata(
            input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
            output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
        )

        assistant_message = ChatMessage(
            role="assistant",
            content="".join(text_parts).strip(),
            tool_calls=tool_calls,
        )

        raw = response.model_dump() if hasattr(response, "model_dump") else None

        return ChatResponse(
            message=assistant_message,
            stop_reason=response.stop_reason or "unknown",
            usage=usage,
            model=response.model,
            provider=self.name,
            tool_calls=tool_calls,
            raw=raw,
        )
