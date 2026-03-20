import uuid
import asyncio

from app.core.config import Settings
from app.domain.models import Conversation, MessageRole, RoutingMode
from app.providers.base import ChatMessage, ChatResponse, ToolCall, UsageMetadata
from app.services.chat_orchestrator import ChatOrchestrator
from app.services.context_manager import ContextManager
from app.services.prompt_builder import PromptBuilder
from app.services.routing_policy import RoutingDecision, RoutingPolicy
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


class FakeProvider:
    def __init__(self):
        self.calls = 0

    async def complete(self, request):
        self.calls += 1
        if self.calls == 1:
            tool_call = ToolCall(id="tool-1", name="list_uploaded_files", arguments={})
            return ChatResponse(
                message=ChatMessage(role="assistant", content="", tool_calls=[tool_call]),
                stop_reason="tool_use",
                usage=UsageMetadata(input_tokens=10, output_tokens=3),
                model="claude-test",
                provider="anthropic",
                tool_calls=[tool_call],
            )
        return ChatResponse(
            message=ChatMessage(role="assistant", content="final"),
            stop_reason="end_turn",
            usage=UsageMetadata(input_tokens=2, output_tokens=2),
            model="claude-test",
            provider="anthropic",
            tool_calls=[],
        )


class FakeToolService:
    def specs(self):
        return []

    async def execute_call(self, *, db, conversation_id, call):
        return ToolExecutionResult(call=call, result={"files": []})


class FakeContextManager(ContextManager):
    pass


def test_tool_loop_executes_and_appends_messages():
    settings = Settings(anthropic_api_key="test-key", max_tool_iterations=3)
    orchestrator = ChatOrchestrator(
        settings=settings,
        prompt_builder=PromptBuilder(),
        routing_policy=RoutingPolicy(settings),
        context_manager=FakeContextManager(settings, rag_service=None),  # type: ignore[arg-type]
        tool_service=FakeToolService(),
    )

    db = FakeDB()
    conversation = Conversation(
        id=uuid.uuid4(),
        title="Test",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        metadata_json={},
    )
    provider = FakeProvider()
    working_messages = [ChatMessage(role="user", content="hello")]
    citations = []

    asyncio.run(
        orchestrator._run_tool_loop(
            db=db,
            conversation=conversation,
            provider=provider,
            decision=RoutingDecision(
                provider="anthropic",
                model="claude-test",
                routing_mode=RoutingMode.POLICY,
                tier="default",
                rationale="test",
            ),
            effective_prompt="system",
            working_messages=working_messages,
            citations=citations,
        )
    )

    assert provider.calls == 2
    assert any(getattr(m, "role", None) == MessageRole.TOOL for m in db.added)
    assert any(msg.role == "tool" for msg in working_messages)
