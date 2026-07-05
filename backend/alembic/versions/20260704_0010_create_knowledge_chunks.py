"""create knowledge chunks

Revision ID: 20260704_0010
Revises: 20260704_0009
Create Date: 2026-07-04
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

revision: str = "20260704_0010"
down_revision: str | None = "20260704_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        embedding_type = pgvector.sqlalchemy.Vector(1536)
    else:
        embedding_type = sa.JSON()

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("knowledge_item_id", sa.UUID(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", embedding_type, nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_item_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_knowledge_chunks_knowledge_item_id",
        "knowledge_chunks",
        ["knowledge_item_id"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_source",
        "knowledge_chunks",
        ["source"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_source", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_knowledge_item_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
