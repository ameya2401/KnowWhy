"""notion integration

Revision ID: 20260703_0006
Revises: 20260703_0005
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260703_0006"
down_revision: str | None = "20260703_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Update integrations provider check constraint
    op.drop_constraint("ck_integrations_provider", "integrations")
    op.create_check_constraint(
        "ck_integrations_provider",
        "integrations",
        "provider IN ('github', 'notion')",
    )

    # Add workspace_id, workspace_name, workspace_icon columns
    op.add_column("integrations", sa.Column("workspace_id", sa.Text(), nullable=True))
    op.add_column("integrations", sa.Column("workspace_name", sa.Text(), nullable=True))
    op.add_column("integrations", sa.Column("workspace_icon", sa.Text(), nullable=True))

    # 2. Create notion_pages table
    op.create_table(
        "notion_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notion_page_id", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("last_edited", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("integration_id", "notion_page_id", name="uq_notion_pages_notion_id"),
    )
    op.create_index("ix_notion_pages_integration_id", "notion_pages", ["integration_id"])


def downgrade() -> None:
    op.drop_index("ix_notion_pages_integration_id", table_name="notion_pages")
    op.drop_table("notion_pages")

    op.drop_column("integrations", "workspace_icon")
    op.drop_column("integrations", "workspace_name")
    op.drop_column("integrations", "workspace_id")

    op.drop_constraint("ck_integrations_provider", "integrations")
    op.create_check_constraint(
        "ck_integrations_provider",
        "integrations",
        "provider = 'github'",
    )
