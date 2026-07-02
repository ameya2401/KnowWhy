"""github integration

Revision ID: 20260703_0005
Revises: 20260703_0004
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260703_0005"
down_revision: str | None = "20260703_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Integrations Table
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("credentials", sa.Text(), nullable=True),
        sa.Column("connected_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("provider = 'github'", name="ck_integrations_provider"),
        sa.CheckConstraint(
            "status in ('connected', 'disconnected', 'syncing', 'error')",
            name="ck_integrations_status",
        ),
        sa.ForeignKeyConstraint(["connected_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "provider", name="uq_integrations_project_provider"),
    )
    op.create_index("ix_integrations_organization_id", "integrations", ["organization_id"])
    op.create_index("ix_integrations_project_id", "integrations", ["project_id"])
    op.create_index("ix_integrations_connected_by_id", "integrations", ["connected_by_id"])

    # 2. Integration Repositories Table
    op.create_table(
        "integration_repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_repo_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("owner", sa.Text(), nullable=False),
        sa.Column("default_branch", sa.Text(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("clone_url", sa.Text(), nullable=False),
        sa.Column("last_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["integration_id"], ["integrations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "integration_id",
            "github_repo_id",
            name="uq_integration_repositories_github_id",
        ),
    )
    op.create_index(
        "ix_integration_repositories_integration_id",
        "integration_repositories",
        ["integration_id"],
    )

    # 3. Integration Commits Table
    op.create_table(
        "integration_commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sha", sa.Text(), nullable=False),
        sa.Column("author_name", sa.Text(), nullable=False),
        sa.Column("author_email", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("commit_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["integration_repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "sha", name="uq_commits_repo_sha"),
    )
    op.create_index(
        "ix_integration_commits_repository_id",
        "integration_commits",
        ["repository_id"],
    )

    # 4. Integration Pull Requests Table
    op.create_table(
        "integration_pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_pr_id", sa.Text(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("created_at_meta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["integration_repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "github_pr_id", name="uq_prs_repo_pr_id"),
    )
    op.create_index(
        "ix_integration_pull_requests_repository_id",
        "integration_pull_requests",
        ["repository_id"],
    )

    # 5. Integration Issues Table
    op.create_table(
        "integration_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_issue_id", sa.Text(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("author", sa.Text(), nullable=False),
        sa.Column("created_at_meta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["integration_repositories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "github_issue_id", name="uq_issues_repo_issue_id"),
    )
    op.create_index(
        "ix_integration_issues_repository_id",
        "integration_issues",
        ["repository_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_integration_issues_repository_id", table_name="integration_issues")
    op.drop_table("integration_issues")

    op.drop_index(
        "ix_integration_pull_requests_repository_id",
        table_name="integration_pull_requests",
    )
    op.drop_table("integration_pull_requests")

    op.drop_index("ix_integration_commits_repository_id", table_name="integration_commits")
    op.drop_table("integration_commits")

    op.drop_index(
        "ix_integration_repositories_integration_id",
        table_name="integration_repositories",
    )
    op.drop_table("integration_repositories")

    op.drop_index("ix_integrations_connected_by_id", table_name="integrations")
    op.drop_index("ix_integrations_project_id", table_name="integrations")
    op.drop_index("ix_integrations_organization_id", table_name="integrations")
    op.drop_table("integrations")
