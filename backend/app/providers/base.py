from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class UsageMetadata:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(slots=True)
class ModelCapabilities:
    model: str
    provider: str
    supports_streaming: bool = True
    supports_tool_calling: bool = True
    supports_vision: bool = False


@dataclass(slots=True)
class ChatMessage:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass(slots=True)
class ChatRequest:
    messages: list[ChatMessage]
    model: str
    system_prompt: str = ""
    temperature: float = 0.2
    max_tokens: int = 1024
    tools: list[ToolSpec] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChatResponse:
    message: ChatMessage
    stop_reason: str
    usage: UsageMetadata
    model: str
    provider: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class StreamEvent:
    type: Literal["text_delta", "tool_call", "usage", "done", "error"]
    delta: str = ""
    tool_call: ToolCall | None = None
    usage: UsageMetadata | None = None
    response: ChatResponse | None = None
    error: str | None = None


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, request: ChatRequest) -> ChatResponse:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        raise NotImplementedError

    @abstractmethod
    def capabilities(self, model: str) -> ModelCapabilities:
        raise NotImplementedError
