"""organization workspace

Revision ID: 20260702_0003
Revises: 20260702_0002
Create Date: 2026-07-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260702_0003"
down_revision: str | None = "20260702_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_created_by_id", "organizations", ["created_by_id"])
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "organization_memberships",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('owner', 'admin', 'member')", name="ck_membership_role"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_org"),
    )
    op.create_index(
        "ix_memberships_organization_id",
        "organization_memberships",
        ["organization_id"],
    )
    op.create_index("ix_memberships_user_id", "organization_memberships", ["user_id"])

    op.create_table(
        "organization_invitations",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("invited_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role in ('admin', 'member')", name="ck_invitation_role"),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_invitations_org_email_active",
        "organization_invitations",
        ["organization_id", "email"],
        postgresql_where=sa.text("accepted_at is null and revoked_at is null"),
    )

    op.add_column(
        "users",
        sa.Column("active_organization_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_users_active_organization_id",
        "users",
        "organizations",
        ["active_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_active_organization_id", "users", type_="foreignkey")
    op.drop_column("users", "active_organization_id")
    op.drop_index("ix_invitations_org_email_active", table_name="organization_invitations")
    op.drop_table("organization_invitations")
    op.drop_index("ix_memberships_user_id", table_name="organization_memberships")
    op.drop_index("ix_memberships_organization_id", table_name="organization_memberships")
    op.drop_table("organization_memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_created_by_id", table_name="organizations")
    op.drop_table("organizations")
