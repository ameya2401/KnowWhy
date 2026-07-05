"""create engineering insights table

Revision ID: 20260705_0013
Revises: 20260705_0012
Create Date: 2026-07-05
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op


revision: str = "20260705_0013"
down_revision: str | None = "20260705_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "engineering_insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("insight_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("suggested_actions", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_engineering_insights_project_id",
        "engineering_insights",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_insights_organization_id",
        "engineering_insights",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_insights_insight_type",
        "engineering_insights",
        ["insight_type"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_insights_severity",
        "engineering_insights",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_engineering_insights_status",
        "engineering_insights",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_engineering_insights_status", table_name="engineering_insights")
    op.drop_index("ix_engineering_insights_severity", table_name="engineering_insights")
    op.drop_index("ix_engineering_insights_insight_type", table_name="engineering_insights")
    op.drop_index("ix_engineering_insights_organization_id", table_name="engineering_insights")
    op.drop_index("ix_engineering_insights_project_id", table_name="engineering_insights")
    op.drop_table("engineering_insights")
