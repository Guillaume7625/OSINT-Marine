import io
import uuid
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.files import router as files_router
from app.core.database import get_db
from app.core.dependencies import get_rag_service
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
        self.committed = False

    def query(self, *args, **kwargs):
        return FakeQuery(self.conversation)

    def commit(self):
        self.committed = True


class FakeRagService:
    def ingest_upload(self, *, db, filename, content_type, content, conversation_id):
        assert filename == "notes.txt"
        assert content_type == "text/plain"
        assert content == b"hello world"
        assert conversation_id
        return SimpleNamespace(id=uuid.uuid4(), filename=filename), 1


def test_file_upload_api_integration_smoke():
    conversation = Conversation(
        id=uuid.uuid4(),
        title="c",
        provider="anthropic",
        routing_mode=RoutingMode.POLICY,
        metadata_json={},
    )
    fake_db = FakeDB(conversation)

    app = FastAPI()
    app.include_router(files_router)

    def override_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_rag_service] = lambda: FakeRagService()

    with TestClient(app) as client:
        response = client.post(
            f"/api/conversations/{conversation.id}/files",
            files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["chunks_created"] == 1
    assert fake_db.committed is True
