import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import MessageRole, RoutingMode


class Citation(BaseModel):
    filename: str
    chunk_index: int
    page_number: int | None = None


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    routing_mode: RoutingMode = RoutingMode.POLICY
    conversation_prompt: str | None = None


class ConversationUpdate(BaseModel):
    title: str | None = None
    routing_mode: RoutingMode | None = None
    locked_model: str | None = None
    manual_model: str | None = None
    conversation_prompt: str | None = None


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    provider: str
    routing_mode: RoutingMode
    locked_model: str | None
    manual_model: str | None
    last_selected_model: str | None
    total_input_tokens: int
    total_output_tokens: int
    total_latency_ms: float
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    tool_name: str | None
    tool_call_id: str | None
    provider: str | None
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: float | None
    citations: list[dict] | None
    created_at: datetime


class ConversationDetail(BaseModel):
    conversation: ConversationRead
    messages: list[MessageRead]
    summary: str | None = None


class ChatTurnRequest(BaseModel):
    message: str = Field(..., min_length=1)
    route_mode: RoutingMode | None = None
    manual_model: str | None = None
    temporary_system_prompt: str | None = None
    task_type: Literal["chat", "rag", "code", "strategy"] = "chat"
    latency_sensitive: bool = False
    require_tools: bool = False
    require_rag: bool = False
    user_model_preference: str | None = None


class UploadResponse(BaseModel):
    file_id: uuid.UUID
    filename: str
    chunks_created: int = 0
    ingestion_status: str = "queued"
    ingestion_error: str | None = None
    ingestion_job_id: uuid.UUID | None = None


class UploadedFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID | None
    filename: str
    content_type: str
    size_bytes: int
    ingestion_status: str
    ingestion_error: str | None = None
    chunks_created: int = 0
    created_at: datetime


class PromptProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    global_prompt: str
    workspace_prompt: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PromptSettingsUpdate(BaseModel):
    global_prompt: str | None = None
    workspace_prompt: str | None = None


class RoutingSettings(BaseModel):
    mode: RoutingMode = RoutingMode.POLICY
    manual_model: str | None = None
    locked_model: str | None = None


class DevSettingsRead(BaseModel):
    prompt_profile: PromptProfileRead
    routing_defaults: dict[str, Any]


class DevSettingsUpdate(BaseModel):
    prompt: PromptSettingsUpdate | None = None
    routing_defaults: dict[str, Any] | None = None
