import uuid
from datetime import datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class RoutingMode(StrEnum):
    POLICY = "policy"
    MANUAL = "manual"
    LOCKED = "locked"


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    provider: Mapped[str] = mapped_column(String(64), default="anthropic")
    routing_mode: Mapped[RoutingMode] = mapped_column(Enum(RoutingMode, name="routing_mode"), default=RoutingMode.POLICY)
    locked_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manual_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_profile_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("prompt_profiles.id"), nullable=True)
    conversation_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_selected_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(back_populates="conversation")
    summary: Mapped["ConversationSummary | None"] = relationship(back_populates="conversation", uselist=False)
    prompt_profile: Mapped["PromptProfile | None"] = relationship(back_populates="conversations")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), index=True)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"), index=True)
    content: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tool_call_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    citations: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    content_type: Mapped[str] = mapped_column(String(128))
    storage_path: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[Conversation | None] = relationship(back_populates="uploaded_files")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="uploaded_file", cascade="all, delete-orphan")
    ingestion_job: Mapped["FileIngestionJob | None"] = relationship(
        back_populates="uploaded_file",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
    )

    @property
    def ingestion_status(self) -> str:
        return str((self.metadata_json or {}).get("ingestion_status", "done"))

    @property
    def ingestion_error(self) -> str | None:
        error = (self.metadata_json or {}).get("ingestion_error")
        return str(error) if error else None

    @property
    def chunks_created(self) -> int:
        try:
            return int((self.metadata_json or {}).get("chunks_created", 0))
        except (TypeError, ValueError):
            return 0


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("uploaded_files.id"), index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    uploaded_file: Mapped[UploadedFile] = relationship(back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("file_id", "chunk_index", name="uq_file_chunk"),
    )


class FileIngestionJob(Base):
    __tablename__ = "file_ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("uploaded_files.id"),
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    uploaded_file: Mapped[UploadedFile] = relationship(back_populates="ingestion_job")


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), unique=True, index=True)
    summary_text: Mapped[str] = mapped_column(Text)
    token_estimate: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="summary")


class PromptProfile(Base):
    __tablename__ = "prompt_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    global_prompt: Mapped[str] = mapped_column(Text, default="")
    workspace_prompt: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    conversations: Mapped[list[Conversation]] = relationship(back_populates="prompt_profile")


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
