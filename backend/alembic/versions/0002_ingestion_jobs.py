"""add file ingestion jobs

Revision ID: 0002_ingestion_jobs
Revises: 0001_initial
Create Date: 2026-04-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_ingestion_jobs"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "file_ingestion_jobs",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("uploaded_file_id", sa.UUID(), sa.ForeignKey("uploaded_files.id"), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'queued'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_file_ingestion_jobs_uploaded_file_id", "file_ingestion_jobs", ["uploaded_file_id"], unique=True)
    op.create_index("ix_file_ingestion_jobs_status", "file_ingestion_jobs", ["status"], unique=False)
    op.create_index("ix_file_ingestion_jobs_queued_at", "file_ingestion_jobs", ["queued_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_file_ingestion_jobs_queued_at", table_name="file_ingestion_jobs")
    op.drop_index("ix_file_ingestion_jobs_status", table_name="file_ingestion_jobs")
    op.drop_index("ix_file_ingestion_jobs_uploaded_file_id", table_name="file_ingestion_jobs")
    op.drop_table("file_ingestion_jobs")
