import asyncio
import uuid

from app.core.config import Settings
from app.domain.models import Conversation, MessageRole, PromptProfile, RoutingMode
from app.providers.base import ChatMessage, ChatResponse, StreamEvent, ToolCall, UsageMetadata
from app.services.chat_orchestrator import ChatOrchestrator, ChatTurnOptions
from app.services.prompt_builder import PromptBuilder
from app.services.routing_policy import RoutingPolicy
from app.services.tool_service import ToolExecutionResult


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    def flush(self):
        return None

    def commit(self):
        return None


class FakeContextManager:
    def build(self, **kwargs):
        return type(
            "ContextBundle",
            (),
            {
                "messages": [ChatMessage(role="user", content=kwargs["user_query"])],
                "summary_memory": None,
                "retrieved_context": None,
                "citations": [],
            },
        )()


class FakeStreamingProvider:
    def __init__(self):
        self.stream_calls = 0

    async def stream(self, request):
        self.stream_calls += 1
        assert request.tools, "tools should be enabled for this test"
        yield StreamEvent(type="text_delta", delta="final answer")
        response = ChatResponse(
            message=ChatMessage(role="assistant", content="final answer"),
            stop_reason="end_turn",
            usage=UsageMetadata(input_tokens=5, output_tokens=7),
            model="claude-test",
            provider="anthropic",
            tool_calls=[],
        )
        yield StreamEvent(type="usage", usage=response.usage)
        yield StreamEvent(type="done", response=response)


class FakeToolCallingStreamingProvider:
    def __init__(self):
        self.stream_calls = 0

    async def stream(self, request):
        self.stream_calls += 1
        assert request.tools, "tools should be enabled for this test"

        if self.stream_calls == 1:
            tool_call = ToolCall(id="tool-1", name="list_uploaded_files", arguments={})
            response = ChatResponse(
                message=ChatMessage(role="assistant", content="", tool_calls=[tool_call]),
                stop_reason="tool_use",
                usage=UsageMetadata(input_tokens=10, output_tokens=3),
                model="claude-test",
                provider="anthropic",
                tool_calls=[tool_call],
            )
            yield StreamEvent(type="tool_call", tool_call=tool_call)
            yield StreamEvent(type="usage", usage=response.usage)
            yield StreamEvent(type="done", response=response)
            return

        response = ChatResponse(
            message=ChatMessage(role="assistant", content="final after tool"),
            stop_reason="end_turn",
            usage=UsageMetadata(input_tokens=6, output_tokens=8),
            model="claude-test",
            provider="anthropic",
            tool_calls=[],
        )
        yield StreamEvent(type="text_delta", delta="final after tool")
        yield StreamEvent(type="usage", usage=response.usage)
        yield StreamEvent(type="done", response=response)


class FakeToolService:
    def specs(self):
        return [
            type(
                "ToolSpec",
                (),
                {"name": "list_uploaded_files", "description": "List files", "input_schema": {"type": "object"}},
            )()
        ]

    async def execute_call(self, *, db, conversation_id, call):
        return ToolExecutionResult(call=call, result={"files": []})


def test_stream_turn_with_tools_uses_single_streaming_pass_when_no_tool_calls(monkeypatch):
    settings = Settings(anthropic_api_key="test-key", max_tool_iterations=3)
    provider = FakeStreamingProvider()
    orchestrator = ChatOrchestrator(
        settings=settings,
        prompt_builder=PromptBuilder(),
        routing_policy=RoutingPolicy(settings),
        context_manager=FakeContextManager(),  # type: ignore[arg-type]
        tool_service=FakeToolService(),
    )
    orchestrator.redis = None

    monkeypatch.setattr("app.services.chat_orchestrator.get_provider", lambda *args, **kwargs: provider)

    db = FakeDB()
    conversation = Conversation(
        id=uuid.uuid4(),
        title="Test",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        prompt_profile=PromptProfile(
            name="default",
            global_prompt="global",
            workspace_prompt="workspace",
            is_active=True,
        ),
        total_input_tokens=0,
        total_output_tokens=0,
        total_latency_ms=0,
        metadata_json={},
    )

    events = asyncio.run(
        _collect_events(
            orchestrator.stream_turn(
                db=db,
                conversation=conversation,
                user_text="hello",
                options=ChatTurnOptions(require_tools=True, require_rag=False),
            )
        )
    )

    assert provider.stream_calls == 1
    assert "".join(event["delta"] for event in events if event["type"] == "token") == "final answer"
    assert any(event["type"] == "done" for event in events)


def test_stream_turn_with_tool_call_stays_on_streaming_path(monkeypatch):
    settings = Settings(anthropic_api_key="test-key", max_tool_iterations=3)
    provider = FakeToolCallingStreamingProvider()
    orchestrator = ChatOrchestrator(
        settings=settings,
        prompt_builder=PromptBuilder(),
        routing_policy=RoutingPolicy(settings),
        context_manager=FakeContextManager(),  # type: ignore[arg-type]
        tool_service=FakeToolService(),
    )
    orchestrator.redis = None

    monkeypatch.setattr("app.services.chat_orchestrator.get_provider", lambda *args, **kwargs: provider)

    db = FakeDB()
    conversation = Conversation(
        id=uuid.uuid4(),
        title="Test",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        prompt_profile=PromptProfile(
            name="default",
            global_prompt="global",
            workspace_prompt="workspace",
            is_active=True,
        ),
        total_input_tokens=0,
        total_output_tokens=0,
        total_latency_ms=0,
        metadata_json={},
    )

    events = asyncio.run(
        _collect_events(
            orchestrator.stream_turn(
                db=db,
                conversation=conversation,
                user_text="hello",
                options=ChatTurnOptions(require_tools=True, require_rag=False),
            )
        )
    )

    assert provider.stream_calls == 2
    assert "".join(event["delta"] for event in events if event["type"] == "token") == "final after tool"
    assert any(getattr(m, "role", None) == MessageRole.TOOL for m in db.added)
    assert any(event["type"] == "done" for event in events)


def test_apply_tool_calls_persists_tool_messages():
    settings = Settings(anthropic_api_key="test-key", max_tool_iterations=3)
    orchestrator = ChatOrchestrator(
        settings=settings,
        prompt_builder=PromptBuilder(),
        routing_policy=RoutingPolicy(settings),
        context_manager=FakeContextManager(),  # type: ignore[arg-type]
        tool_service=FakeToolService(),
    )
    orchestrator.redis = None

    db = FakeDB()
    conversation = Conversation(
        id=uuid.uuid4(),
        title="Test",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        total_input_tokens=0,
        total_output_tokens=0,
        total_latency_ms=0,
        metadata_json={},
    )
    working_messages = [ChatMessage(role="user", content="hello")]
    citations = []
    tool_call = ToolCall(id="tool-1", name="list_uploaded_files", arguments={})
    response = ChatResponse(
        message=ChatMessage(role="assistant", content="", tool_calls=[tool_call]),
        stop_reason="tool_use",
        usage=UsageMetadata(input_tokens=10, output_tokens=3),
        model="claude-test",
        provider="anthropic",
        tool_calls=[tool_call],
    )

    asyncio.run(
        orchestrator._apply_tool_calls(
            db=db,
            conversation=conversation,
            decision=type(
                "Decision",
                (),
                {"provider": "anthropic", "model": "claude-test"},
            )(),
            response=response,
            working_messages=working_messages,
            citations=citations,
        )
    )

    assert any(getattr(m, "role", None) == MessageRole.TOOL for m in db.added)
    assert any(msg.role == "tool" for msg in working_messages)


async def _collect_events(stream):
    events = []
    async for event in stream:
        events.append(event)
    return events
