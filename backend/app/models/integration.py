import enum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class IntegrationProvider(str, enum.Enum):
    GITHUB = "github"


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SYNCING = "syncing"
    ERROR = "error"


class Integration(BaseModel):
    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("project_id", "provider", name="uq_integrations_project_provider"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(
            IntegrationProvider,
            native_enum=False,
            values_callable=lambda enum_: [e.value for e in enum_],
        ),
        nullable=False,
    )
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(
            IntegrationStatus,
            native_enum=False,
            values_callable=lambda enum_: [e.value for e in enum_],
        ),
        default=IntegrationStatus.CONNECTED,
        nullable=False,
    )
    # Encrypted credentials JSON string
    credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    connected_by_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    repositories: Mapped[list["IntegrationRepository"]] = relationship(
        back_populates="integration",
        cascade="all, delete-orphan",
    )


class IntegrationRepository(BaseModel):
    __tablename__ = "integration_repositories"
    __table_args__ = (
        UniqueConstraint(
            "integration_id",
            "github_repo_id",
            name="uq_integration_repositories_github_id",
        ),
    )

    integration_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    github_repo_id: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(Text, nullable=False)  # "public" or "private"
    clone_url: Mapped[str] = mapped_column(Text, nullable=False)
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    integration: Mapped[Integration] = relationship(back_populates="repositories")
    commits: Mapped[list["Commit"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    issues: Mapped[list["Issue"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class Commit(BaseModel):
    __tablename__ = "integration_commits"
    __table_args__ = (UniqueConstraint("repository_id", "sha", name="uq_commits_repo_sha"),)

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("integration_repositories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sha: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str] = mapped_column(Text, nullable=False)
    author_email: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    commit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    repository: Mapped[IntegrationRepository] = relationship(back_populates="commits")


class PullRequest(BaseModel):
    __tablename__ = "integration_pull_requests"
    __table_args__ = (UniqueConstraint("repository_id", "github_pr_id", name="uq_prs_repo_pr_id"),)

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("integration_repositories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    github_pr_id: Mapped[str] = mapped_column(Text, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)  # "open", "closed", etc.
    author: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_meta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped[IntegrationRepository] = relationship(back_populates="pull_requests")


class Issue(BaseModel):
    __tablename__ = "integration_issues"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_issue_id", name="uq_issues_repo_issue_id"),
    )

    repository_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("integration_repositories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    github_issue_id: Mapped[str] = mapped_column(Text, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False)  # "open", "closed", etc.
    author: Mapped[str] = mapped_column(Text, nullable=False)
    created_at_meta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    repository: Mapped[IntegrationRepository] = relationship(back_populates="issues")
