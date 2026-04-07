from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.domain.models import ConversationSummary, Message
from app.providers.base import ChatMessage
from app.services.rag_service import RagService


@dataclass(slots=True)
class ContextBundle:
    messages: list[ChatMessage]
    summary_memory: str | None = None
    retrieved_context: str | None = None
    citations: list[dict] = field(default_factory=list)


class ContextManager:
    def __init__(self, settings: Settings, rag_service: RagService):
        self.settings = settings
        self.rag_service = rag_service

    def build(
        self,
        *,
        db: Session,
        conversation_id: uuid.UUID,
        user_query: str,
        require_rag: bool,
    ) -> ContextBundle:
        summary_memory = self._get_existing_summary(db=db, conversation_id=conversation_id)
        recent_messages = self._load_recent_messages(
            db=db,
            conversation_id=conversation_id,
            limit=self.settings.default_context_window_messages,
        )

        if len(recent_messages) >= self.settings.default_context_window_messages:
            rebuilt_summary = self._build_summary_from_recent_history(
                db=db,
                conversation_id=conversation_id,
            )
            if rebuilt_summary is not None:
                summary_memory = rebuilt_summary

        normalized_messages: list[ChatMessage] = []
        for item in recent_messages:
            normalized_messages.append(
                ChatMessage(
                    role=item.role.value,
                    content=item.content,
                    tool_call_id=item.tool_call_id,
                    tool_name=item.tool_name,
                )
            )

        retrieved_context = None
        citations: list[dict] = []
        if require_rag:
            hits = self.rag_service.retrieve(
                db=db,
                query=user_query,
                conversation_id=str(conversation_id),
                top_k=self.settings.rag_top_k,
            )
            if hits:
                lines: list[str] = []
                for hit in hits:
                    citation = {
                        "filename": hit["filename"],
                        "chunk_index": hit["chunk_index"],
                        "page_number": hit.get("page_number"),
                    }
                    citations.append(citation)
                    lines.append(
                        (
                            f"[source={hit['filename']} chunk={hit['chunk_index']} page={hit.get('page_number')}]"
                            f" {hit['content']}"
                        )
                    )
                retrieved_context = "\n".join(lines)

        return ContextBundle(
            messages=normalized_messages,
            summary_memory=summary_memory,
            retrieved_context=retrieved_context,
            citations=citations,
        )

    def _load_recent_messages(
        self,
        *,
        db: Session,
        conversation_id: uuid.UUID,
        limit: int,
    ) -> list[Message]:
        rows = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        rows.reverse()
        return rows

    def _get_existing_summary(self, *, db: Session, conversation_id: uuid.UUID) -> str | None:
        existing = (
            db.query(ConversationSummary)
            .filter(ConversationSummary.conversation_id == conversation_id)
            .one_or_none()
        )
        return existing.summary_text if existing else None

    def _build_summary_from_recent_history(self, *, db: Session, conversation_id: uuid.UUID) -> str | None:
        summary_window = self.settings.default_context_window_messages + 20
        recent_candidates = self._load_recent_messages(
            db=db,
            conversation_id=conversation_id,
            limit=summary_window,
        )
        if len(recent_candidates) <= self.settings.default_context_window_messages + 6:
            return None

        older = recent_candidates[: -self.settings.default_context_window_messages]
        if not older:
            return None

        summary_lines: list[str] = []
        for msg in older[-20:]:
            role = msg.role.value
            content = " ".join(msg.content.split())
            summary_lines.append(f"{role}: {content[:220]}")

        summary_text = "\n".join(summary_lines)

        existing = (
            db.query(ConversationSummary)
            .filter(ConversationSummary.conversation_id == conversation_id)
            .one_or_none()
        )
        if existing:
            existing.summary_text = summary_text
            existing.token_estimate = max(1, len(summary_text) // 4)
        else:
            db.add(
                ConversationSummary(
                    conversation_id=conversation_id,
                    summary_text=summary_text,
                    token_estimate=max(1, len(summary_text) // 4),
                )
            )

        db.flush()
        return summary_text
