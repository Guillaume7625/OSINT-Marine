from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_rag_service
from app.domain.models import Conversation, UploadedFile
from app.domain.schemas import UploadResponse, UploadedFileRead
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/conversations", tags=["files"])
SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


@router.post("/{conversation_id}/files", response_model=UploadResponse)
async def upload_file(
    conversation_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    rag_service: RagService = Depends(get_rag_service),
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = "." + file.filename.rsplit(".", maxsplit=1)[-1].lower() if "." in file.filename else ""
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    content = await file.read()
    uploaded, chunks = rag_service.ingest_upload(
        db=db,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        content=content,
        conversation_id=str(conversation_id),
    )
    db.commit()

    return UploadResponse(file_id=uploaded.id, filename=uploaded.filename, chunks_created=chunks)


@router.get("/{conversation_id}/files", response_model=list[UploadedFileRead])
def list_files(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.conversation_id == conversation_id)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return files
