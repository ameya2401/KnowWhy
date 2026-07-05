"""add search indexes

Revision ID: 20260704_0009
Revises: 20260703_0008
Create Date: 2026-07-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260704_0009"
down_revision: str | None = "20260703_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_knowledge_items_title", "knowledge_items", ["title"])

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Create pg_trgm extension if not exists for fast wildcard ILIKE matching
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        # Create GIN indexes for fast fuzzy search on title and content
        op.execute(
            "CREATE INDEX ix_knowledge_items_title_trgm ON "
            "knowledge_items USING gin (title gin_trgm_ops)"
        )
        op.execute(
            "CREATE INDEX ix_knowledge_items_content_trgm ON "
            "knowledge_items USING gin (content gin_trgm_ops)"
        )
        # Create GIN index on tags
        op.execute("CREATE INDEX ix_knowledge_items_tags_gin ON knowledge_items USING gin (tags)")
    else:
        # Standard indexes for SQLite or others
        op.create_index("ix_knowledge_items_content", "knowledge_items", ["content"])
        op.create_index("ix_knowledge_items_tags", "knowledge_items", ["tags"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_knowledge_items_title_trgm")
        op.execute("DROP INDEX IF EXISTS ix_knowledge_items_content_trgm")
        op.execute("DROP INDEX IF EXISTS ix_knowledge_items_tags_gin")
    else:
        op.drop_index("ix_knowledge_items_content", table_name="knowledge_items")
        op.drop_index("ix_knowledge_items_tags", table_name="knowledge_items")
    op.drop_index("ix_knowledge_items_title", table_name="knowledge_items")
