"""create ai chat tables

Revision ID: 20260705_0011
Revises: 20260704_0010
Create Date: 2026-07-05
"""

from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260705_0011"
down_revision: str | None = "20260704_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False, server_default="openai"),
        sa.Column("model", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("citation_mode", sa.Text(), nullable=False, server_default="grounded"),
        sa.Column("streaming_on", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_conversations_project_id",
        "ai_conversations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_conversations_user_id",
        "ai_conversations",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ai_messages_conversation_id",
        "ai_messages",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_messages_conversation_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_user_id", table_name="ai_conversations")
    op.drop_index("ix_ai_conversations_project_id", table_name="ai_conversations")
    op.drop_table("ai_conversations")
