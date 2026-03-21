from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_chat_orchestrator
from app.domain.models import Conversation
from app.domain.schemas import ChatTurnRequest
from app.services.chat_orchestrator import ChatOrchestrator, ChatTurnOptions

router = APIRouter(prefix="/api/conversations", tags=["chat"])
logger = logging.getLogger(__name__)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, default=str)}\\n\\n"


@router.post("/{conversation_id}/chat/stream")
async def stream_chat(
    conversation_id: uuid.UUID,
    payload: ChatTurnRequest,
    db: Session = Depends(get_db),
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    options = ChatTurnOptions(
        route_mode=payload.route_mode,
        manual_model=payload.manual_model,
        temporary_system_prompt=payload.temporary_system_prompt,
        task_type=payload.task_type,
        latency_sensitive=payload.latency_sensitive,
        require_tools=payload.require_tools,
        require_rag=payload.require_rag,
        user_model_preference=payload.user_model_preference,
    )

    async def event_gen():
        try:
            async for event in orchestrator.stream_turn(
                db=db,
                conversation=conversation,
                user_text=payload.message,
                options=options,
            ):
                yield _sse(event)
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            logger.exception("Streaming chat failed for conversation_id=%s", conversation_id, exc_info=exc)
            yield _sse({"type": "error", "error": "Streaming request failed"})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
