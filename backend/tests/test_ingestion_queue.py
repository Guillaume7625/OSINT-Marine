from datetime import datetime, timezone
from types import SimpleNamespace

from app.domain.models import FileIngestionJob, UploadedFile
from app.services.ingestion_queue import IngestionQueueService


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)
        self.with_for_update_kwargs = None

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def with_for_update(self, **kwargs):
        self.with_for_update_kwargs = kwargs
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)


class FakeSession:
    def __init__(self, *, jobs, files):
        self.jobs = list(jobs)
        self.jobs_by_id = {job.id: job for job in jobs}
        self.files = dict(files)
        self.committed = False
        self.added = []
        self.last_query = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def query(self, model):
        if model is FileIngestionJob:
            self.last_query = FakeQuery(self.jobs)
            return self.last_query
        raise AssertionError(f"Unexpected query model: {model!r}")

    def get(self, model, key):
        if model is FileIngestionJob:
            return self.jobs_by_id.get(key)
        if model is UploadedFile:
            return self.files.get(key)
        raise AssertionError(f"Unexpected get model: {model!r}")

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed = True

    def rollback(self):
        return None


class SessionFactory:
    def __init__(self, sessions):
        self.sessions = list(sessions)

    def __call__(self):
        if not self.sessions:
            raise AssertionError("SessionFactory exhausted")
        return self.sessions.pop(0)


def test_recover_in_progress_jobs_keeps_completed_uploads_done(monkeypatch):
    job = SimpleNamespace(
        id="job-1",
        uploaded_file_id="file-1",
        status="processing",
        attempts=1,
        started_at=datetime.now(timezone.utc),
        completed_at=None,
        last_error="stale",
    )
    uploaded_file = SimpleNamespace(
        id="file-1",
        ingestion_status="done",
        ingestion_error=None,
        chunks_created=4,
        metadata_json={"ingestion_status": "done", "chunks_created": 4},
    )
    session = FakeSession(jobs=[job], files={uploaded_file.id: uploaded_file})
    monkeypatch.setattr("app.services.ingestion_queue.SessionLocal", lambda: session)

    queue = IngestionQueueService(rag_service=SimpleNamespace())
    queue.recover_in_progress_jobs()

    assert job.status == "done"
    assert job.completed_at is not None
    assert session.committed is True


def test_process_next_job_claims_rows_with_skip_locked(monkeypatch):
    job = SimpleNamespace(
        id="job-1",
        uploaded_file_id="file-1",
        status="queued",
        attempts=0,
        started_at=None,
        completed_at=None,
        last_error=None,
        queued_at=datetime.now(timezone.utc),
    )
    uploaded_file = SimpleNamespace(
        id="file-1",
        ingestion_status="queued",
        ingestion_error=None,
        chunks_created=3,
        metadata_json={"ingestion_status": "queued", "chunks_created": 3},
    )
    claim_session = FakeSession(jobs=[job], files={uploaded_file.id: uploaded_file})
    finalize_session = FakeSession(jobs=[job], files={uploaded_file.id: uploaded_file})
    monkeypatch.setattr("app.services.ingestion_queue.SessionLocal", SessionFactory([claim_session, finalize_session]))

    queue = IngestionQueueService(rag_service=SimpleNamespace(process_uploaded_file=lambda uploaded_file_id: "done"))
    processed = queue.process_next_job()

    assert processed is True
    assert claim_session.last_query is not None
    assert claim_session.last_query.with_for_update_kwargs == {"skip_locked": True}
    assert job.status == "done"
    assert job.attempts == 1
    assert uploaded_file.metadata_json["ingestion_status"] == "done"
    assert finalize_session.committed is True
