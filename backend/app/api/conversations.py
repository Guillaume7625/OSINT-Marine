from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.domain.models import Conversation, ConversationSummary, Message, PromptProfile
from app.domain.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def list_conversations(db: Session = Depends(get_db)):
    rows = db.query(Conversation).order_by(Conversation.updated_at.desc()).all()
    return rows


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    profile = db.query(PromptProfile).filter(PromptProfile.is_active.is_(True)).first()
    settings = get_settings()
    if not profile:
        profile = PromptProfile(
            name="default",
            global_prompt=settings.bootstrap_global_prompt,
            workspace_prompt=settings.bootstrap_workspace_prompt,
            is_active=True,
        )
        db.add(profile)
        db.flush()

    conv = Conversation(
        title=payload.title,
        provider=settings.default_provider,
        routing_mode=payload.routing_mode,
        conversation_prompt=payload.conversation_prompt,
        prompt_profile_id=profile.id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(conversation_id: uuid.UUID, payload: ConversationUpdate, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(conv, key, value)

    db.commit()
    db.refresh(conv)
    return conv


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    summary = (
        db.query(ConversationSummary)
        .filter(ConversationSummary.conversation_id == conversation_id)
        .one_or_none()
    )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return ConversationDetail(
        conversation=ConversationRead.model_validate(conv),
        messages=[MessageRead.model_validate(m) for m in messages],
        summary=summary.summary_text if summary else None,
    )
