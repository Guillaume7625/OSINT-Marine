from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.domain.models import ConversationSummary


def get_conversation_summary_tool(*, db: Session, conversation_id: str) -> dict:
    conv_uuid = uuid.UUID(conversation_id)
    summary = (
        db.query(ConversationSummary)
        .filter(ConversationSummary.conversation_id == conv_uuid)
        .one_or_none()
    )
    return {
        "conversation_id": conversation_id,
        "summary": summary.summary_text if summary else "No summary available yet.",
    }
