import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.chat import router as chat_router
from app.core.database import get_db
from app.core.dependencies import get_chat_orchestrator
from app.domain.models import Conversation, RoutingMode


class FakeQuery:
    def __init__(self, conversation):
        self.conversation = conversation

    def filter(self, *args, **kwargs):
        return self

    def one_or_none(self):
        return self.conversation


class FakeDB:
    def __init__(self, conversation):
        self.conversation = conversation

    def query(self, *args, **kwargs):
        return FakeQuery(self.conversation)

    def rollback(self):
        return None


class FakeOrchestrator:
    async def stream_turn(self, **kwargs):
        yield {"type": "meta", "model": "claude-test", "provider": "anthropic"}
        yield {"type": "token", "delta": "hello"}
        yield {"type": "done", "usage": {"total_tokens": 1}}


def test_streaming_endpoint_smoke():
    conversation = Conversation(
        id=uuid.uuid4(),
        title="c",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        metadata_json={},
    )
    fake_db = FakeDB(conversation)

    app = FastAPI()
    app.include_router(chat_router)

    def override_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_chat_orchestrator] = lambda: FakeOrchestrator()

    with TestClient(app) as client:
        response = client.post(
            f"/api/conversations/{conversation.id}/chat/stream",
            json={"message": "hello", "require_tools": False, "require_rag": False},
        )

    assert response.status_code == 200
    assert "\"type\": \"token\"" in response.text
    assert "\"type\": \"done\"" in response.text
