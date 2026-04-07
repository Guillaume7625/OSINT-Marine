import io
import uuid
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.files import router as files_router
from app.core.database import get_db
from app.core.dependencies import get_ingestion_queue, get_rag_service
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
    def __init__(self):
        self.storage = SimpleNamespace(save_stream=self._save_stream)
        self.saved_content = None
        self.processed_upload_id = None

    def _save_stream(self, *, filename, stream):
        payload = stream.read()
        self.saved_content = (filename, payload)
        return Path("/tmp/fake-upload.txt"), len(payload)

    def register_upload(self, *, db, filename, content_type, storage_path, size_bytes, conversation_id):
        assert filename == "notes.txt"
        assert content_type == "text/plain"
        assert size_bytes == len(b"hello world")
        assert conversation_id
        return SimpleNamespace(
            id=uuid.uuid4(),
            filename=filename,
            ingestion_status="queued",
            metadata_json={"ingestion_status": "queued", "chunks_created": 0},
        )

    def process_uploaded_file(self, uploaded_file_id):
        self.processed_upload_id = uploaded_file_id


class FakeQueue:
    def __init__(self):
        self.enqueued = []

    def enqueue(self, *, db, uploaded_file):
        self.enqueued.append(uploaded_file.id)
        return SimpleNamespace(id=uuid.uuid4())


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
    fake_rag = FakeRagService()
    fake_queue = FakeQueue()

    def override_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_rag_service] = lambda: fake_rag
    app.dependency_overrides[get_ingestion_queue] = lambda: fake_queue

    with TestClient(app) as client:
        response = client.post(
            f"/api/conversations/{conversation.id}/files",
            files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["chunks_created"] == 0
    assert body["ingestion_status"] == "queued"
    assert body["ingestion_job_id"] is not None
    assert fake_db.committed is True
    assert fake_rag.saved_content == ("notes.txt", b"hello world")
    assert fake_queue.enqueued
