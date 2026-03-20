from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.domain.models import UploadedFile


def list_uploaded_files_tool(*, db: Session, conversation_id: str) -> dict:
    conv_uuid = uuid.UUID(conversation_id)
    files = (
        db.query(UploadedFile)
        .filter(UploadedFile.conversation_id == conv_uuid)
        .order_by(UploadedFile.created_at.desc())
        .all()
    )
    return {
        "conversation_id": conversation_id,
        "files": [
            {
                "file_id": str(f.id),
                "filename": f.filename,
                "content_type": f.content_type,
                "size_bytes": f.size_bytes,
            }
            for f in files
        ],
    }
