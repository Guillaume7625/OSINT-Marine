from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_ingestion_queue, get_rag_service
from app.domain.models import Conversation, UploadedFile
from app.domain.schemas import UploadResponse, UploadedFileRead
from app.services.ingestion_queue import IngestionQueueService
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/conversations", tags=["files"])
SUPPORTED_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".md", ".pdf", ".png", ".tif", ".tiff", ".txt", ".webp"}


@router.post("/{conversation_id}/files", response_model=UploadResponse, status_code=202)
async def upload_file(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    rag_service: RagService = Depends(get_rag_service),
    ingestion_queue: IngestionQueueService = Depends(get_ingestion_queue),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = "." + file.filename.rsplit(".", maxsplit=1)[-1].lower() if "." in file.filename else ""
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    storage_path, size_bytes = rag_service.storage.save_stream(filename=file.filename, stream=file.file)
    uploaded = rag_service.register_upload(
        db=db,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=storage_path,
        size_bytes=size_bytes,
        conversation_id=conversation_id,
    )
    job = ingestion_queue.enqueue(db=db, uploaded_file=uploaded)
    db.commit()

    return UploadResponse(
        file_id=uploaded.id,
        filename=uploaded.filename,
        chunks_created=0,
        ingestion_status=uploaded.ingestion_status,
        ingestion_job_id=job.id,
    )


@router.get("/{conversation_id}/files", response_model=list[UploadedFileRead])
def list_files(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.conversation_id == conversation_id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return files
