"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

routing_mode = postgresql.ENUM(
    "policy",
    "manual",
    "locked",
    name="routing_mode",
    create_type=False,
)

message_role = postgresql.ENUM(
    "system",
    "user",
    "assistant",
    "tool",
    name="message_role",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    routing_mode.create(op.get_bind(), checkfirst=True)
    message_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "prompt_profiles",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("global_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("workspace_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_prompt_profiles_name", "prompt_profiles", ["name"], unique=True)
    op.create_index("ix_prompt_profiles_is_active", "prompt_profiles", ["is_active"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("routing_mode", routing_mode, nullable=False),
        sa.Column("locked_model", sa.String(length=128), nullable=True),
        sa.Column("manual_model", sa.String(length=128), nullable=True),
        sa.Column("prompt_profile_id", sa.UUID(), sa.ForeignKey("prompt_profiles.id"), nullable=True),
        sa.Column("conversation_prompt", sa.Text(), nullable=True),
        sa.Column("last_selected_model", sa.String(length=128), nullable=True),
        sa.Column("total_input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=128), nullable=True),
        sa.Column("tool_call_id", sa.String(length=128), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("citations", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)
    op.create_index("ix_messages_role", "messages", ["role"], unique=False)
    op.create_index("ix_messages_created_at", "messages", ["created_at"], unique=False)

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_uploaded_files_conversation_id", "uploaded_files", ["conversation_id"], unique=False)
    op.create_index("ix_uploaded_files_filename", "uploaded_files", ["filename"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("file_id", sa.UUID(), sa.ForeignKey("uploaded_files.id"), nullable=False),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("file_id", "chunk_index", name="uq_file_chunk"),
    )
    op.create_index("ix_document_chunks_file_id", "document_chunks", ["file_id"], unique=False)
    op.create_index("ix_document_chunks_conversation_id", "document_chunks", ["conversation_id"], unique=False)

    op.create_table(
        "conversation_summaries",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.UUID(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_conversation_summaries_conversation_id",
        "conversation_summaries",
        ["conversation_id"],
        unique=True,
    )

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=128), primary_key=True, nullable=False),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("app_settings")

    op.drop_index("ix_conversation_summaries_conversation_id", table_name="conversation_summaries")
    op.drop_table("conversation_summaries")

    op.drop_index("ix_document_chunks_conversation_id", table_name="document_chunks")
    op.drop_index("ix_document_chunks_file_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_uploaded_files_filename", table_name="uploaded_files")
    op.drop_index("ix_uploaded_files_conversation_id", table_name="uploaded_files")
    op.drop_table("uploaded_files")

    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_role", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_table("conversations")

    op.drop_index("ix_prompt_profiles_is_active", table_name="prompt_profiles")
    op.drop_index("ix_prompt_profiles_name", table_name="prompt_profiles")
    op.drop_table("prompt_profiles")

    message_role.drop(op.get_bind(), checkfirst=True)
    routing_mode.drop(op.get_bind(), checkfirst=True)
