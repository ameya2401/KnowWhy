"""google drive integration

Revision ID: 20260703_0007
Revises: 20260703_0006
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260703_0007"
down_revision: str | None = "20260703_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update integrations provider check constraint
    op.drop_constraint("ck_integrations_provider", "integrations")
    op.create_check_constraint(
        "ck_integrations_provider",
        "integrations",
        "provider IN ('github', 'notion', 'google_drive')",
    )

    # 2. Create drive_files table
    op.create_table(
        "drive_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_file_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("parent_folder", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("owner", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("modified_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "integration_id", "google_file_id", name="uq_drive_files_google_file_id"
        ),
    )
    op.create_index("ix_drive_files_integration_id", "drive_files", ["integration_id"])


def downgrade() -> None:
    op.drop_index("ix_drive_files_integration_id", table_name="drive_files")
    op.drop_table("drive_files")

    op.drop_constraint("ck_integrations_provider", "integrations")
    op.create_check_constraint(
        "ck_integrations_provider",
        "integrations",
        "provider IN ('github', 'notion')",
    )
