from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.domain.models import FileIngestionJob, UploadedFile
from app.services.rag_service import RagService


class IngestionQueueService:
    def __init__(self, rag_service: RagService, poll_interval_seconds: float = 1.0):
        self.rag_service = rag_service
        self.poll_interval_seconds = poll_interval_seconds

    def enqueue(self, *, db: Session, uploaded_file: UploadedFile) -> FileIngestionJob:
        job = db.query(FileIngestionJob).filter(FileIngestionJob.uploaded_file_id == uploaded_file.id).one_or_none()
        if job is None:
            job = FileIngestionJob(uploaded_file_id=uploaded_file.id)
            db.add(job)
        else:
            job.status = "queued"
            job.last_error = None
            job.started_at = None
            job.completed_at = None

        self._set_uploaded_file_status(uploaded_file, status="queued", db=db)
        db.flush()
        return job

    def recover_in_progress_jobs(self) -> None:
        with SessionLocal() as db:
            jobs = db.query(FileIngestionJob).filter(FileIngestionJob.status == "processing").all()
            if not jobs:
                return

            now = datetime.now(timezone.utc)
            for job in jobs:
                uploaded_file = db.get(UploadedFile, job.uploaded_file_id)
                job.started_at = None
                if not uploaded_file:
                    job.status = "error"
                    job.completed_at = now
                    job.last_error = "Uploaded file missing"
                    continue

                if uploaded_file.ingestion_status == "done":
                    job.status = "done"
                    job.completed_at = now
                    job.last_error = None
                    continue

                if uploaded_file.ingestion_status == "error":
                    job.status = "error"
                    job.completed_at = now
                    job.last_error = uploaded_file.ingestion_error or "Ingestion failed"
                    continue

                job.status = "queued"
                job.completed_at = None
                job.last_error = None
                self._set_uploaded_file_status(uploaded_file, status="queued", db=db)

            db.commit()

    def process_next_job(self) -> bool:
        with SessionLocal() as db:
            job = (
                db.query(FileIngestionJob)
                .filter(FileIngestionJob.status == "queued")
                .order_by(FileIngestionJob.queued_at.asc())
                .with_for_update(skip_locked=True)
                .first()
            )
            if job is None:
                return False

            job.status = "processing"
            job.attempts += 1
            job.started_at = datetime.now(timezone.utc)
            job.last_error = None
            uploaded_file = db.get(UploadedFile, job.uploaded_file_id)
            if uploaded_file:
                self._set_uploaded_file_status(uploaded_file, status="processing", db=db)
            db.commit()

            try:
                result = self.rag_service.process_uploaded_file(str(job.uploaded_file_id))
            except Exception as exc:  # noqa: BLE001
                with SessionLocal() as error_db:
                    error_job = error_db.get(FileIngestionJob, job.id)
                    error_file = error_db.get(UploadedFile, job.uploaded_file_id)
                    if error_job:
                        error_job.status = "error"
                        error_job.completed_at = datetime.now(timezone.utc)
                        error_job.last_error = str(exc)
                    if error_file:
                        self._set_uploaded_file_status(error_file, status="error", error=str(exc), db=error_db)
                    error_db.commit()
                return True

        with SessionLocal() as db:
            job = db.get(FileIngestionJob, job.id)
            if not job:
                return True

            uploaded_file = db.get(UploadedFile, job.uploaded_file_id)
            now = datetime.now(timezone.utc)
            if result == "done":
                job.status = "done"
                job.completed_at = now
                job.last_error = None
                if uploaded_file:
                    self._set_uploaded_file_status(
                        uploaded_file,
                        status="done",
                        chunks_created=uploaded_file.chunks_created,
                        db=db,
                    )
            elif result == "missing":
                job.status = "error"
                job.completed_at = now
                job.last_error = "Uploaded file missing"
                if uploaded_file:
                    self._set_uploaded_file_status(uploaded_file, status="error", error=job.last_error, db=db)
            else:
                job.status = "error"
                job.completed_at = now
                if uploaded_file:
                    job.last_error = uploaded_file.ingestion_error or "Ingestion failed"
                    self._set_uploaded_file_status(uploaded_file, status="error", error=job.last_error, db=db)
                else:
                    job.last_error = "Ingestion failed"

            db.commit()
        return True

    async def run_forever(self) -> None:
        while True:
            processed_any = await asyncio.to_thread(self._drain_once)
            if not processed_any:
                await asyncio.sleep(self.poll_interval_seconds)

    def _drain_once(self) -> bool:
        processed_any = False
        while self.process_next_job():
            processed_any = True
        return processed_any

    def _set_uploaded_file_status(
        self,
        uploaded_file: UploadedFile,
        *,
        status: str,
        db: Session,
        error: str | None = None,
        chunks_created: int | None = None,
    ) -> None:
        metadata = dict(uploaded_file.metadata_json or {})
        metadata["ingestion_status"] = status
        if error is not None:
            metadata["ingestion_error"] = error
        elif status != "error":
            metadata["ingestion_error"] = None
        if chunks_created is not None:
            metadata["chunks_created"] = chunks_created
        uploaded_file.metadata_json = metadata
        db.add(uploaded_file)
