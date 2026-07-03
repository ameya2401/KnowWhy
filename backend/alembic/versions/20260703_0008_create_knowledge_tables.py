"""create knowledge tables

Revision ID: 20260703_0008
Revises: 20260703_0007
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260703_0008"
down_revision: str | None = "20260703_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create knowledge_items table
    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_entity_id", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("author", sa.Text(), nullable=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "source",
            "source_entity_id",
            name="uq_knowledge_items_project_source_entity",
        ),
    )
    op.create_index("ix_knowledge_items_organization_id", "knowledge_items", ["organization_id"])
    op.create_index("ix_knowledge_items_project_id", "knowledge_items", ["project_id"])
    op.create_index("ix_knowledge_items_source", "knowledge_items", ["source"])
    op.create_index("ix_knowledge_items_entity_type", "knowledge_items", ["entity_type"])
    op.create_index("ix_knowledge_items_updated_time", "knowledge_items", ["updated_time"])

    # 2. Create knowledge_relationships table
    op.create_table(
        "knowledge_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_item_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_item_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_item_id",
            "target_item_id",
            "relationship_type",
            name="uq_knowledge_relationships_source_target_type",
        ),
    )
    op.create_index(
        "ix_knowledge_relationships_source_item_id", "knowledge_relationships", ["source_item_id"]
    )
    op.create_index(
        "ix_knowledge_relationships_target_item_id", "knowledge_relationships", ["target_item_id"]
    )

    # 3. Create knowledge_sync_logs table
    op.create_table(
        "knowledge_sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("items_synced", sa.Integer(), nullable=False),
        sa.Column("relationships_created", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_sync_logs_project_id", "knowledge_sync_logs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_sync_logs_project_id", table_name="knowledge_sync_logs")
    op.drop_table("knowledge_sync_logs")

    op.drop_index("ix_knowledge_relationships_target_item_id", table_name="knowledge_relationships")
    op.drop_index("ix_knowledge_relationships_source_item_id", table_name="knowledge_relationships")
    op.drop_table("knowledge_relationships")

    op.drop_index("ix_knowledge_items_updated_time", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_entity_type", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_source", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_project_id", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_organization_id", table_name="knowledge_items")
    op.drop_table("knowledge_items")
