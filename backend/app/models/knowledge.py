from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class KnowledgeItem(BaseModel):
    __tablename__ = "knowledge_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "source",
            "source_entity_id",
            name="uq_knowledge_items_project_source_entity",
        ),
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
    source: Mapped[str] = mapped_column(
        Text, index=True, nullable=False
    )  # "github", "notion", "google_drive"
    source_entity_id: Mapped[str] = mapped_column(Text, nullable=False)  # SHA, Page ID, File ID
    entity_type: Mapped[str] = mapped_column(
        Text, index=True, nullable=False
    )  # "commit", "pull_request", "issue", "notion_page", "document", "folder"
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        Text, default="active", nullable=False
    )  # "active", "archived"

    outgoing_relationships: Mapped[list["KnowledgeRelationship"]] = relationship(
        "KnowledgeRelationship",
        foreign_keys="[KnowledgeRelationship.source_item_id]",
        back_populates="source_item",
        cascade="all, delete-orphan",
    )
    incoming_relationships: Mapped[list["KnowledgeRelationship"]] = relationship(
        "KnowledgeRelationship",
        foreign_keys="[KnowledgeRelationship.target_item_id]",
        back_populates="target_item",
        cascade="all, delete-orphan",
    )


class KnowledgeRelationship(BaseModel):
    __tablename__ = "knowledge_relationships"
    __table_args__ = (
        UniqueConstraint(
            "source_item_id",
            "target_item_id",
            "relationship_type",
            name="uq_knowledge_relationships_source_target_type",
        ),
    )

    source_item_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_item_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # "contains", "fixes", "references", "mentions"
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    source_item: Mapped[KnowledgeItem] = relationship(
        "KnowledgeItem",
        foreign_keys=[source_item_id],
        back_populates="outgoing_relationships",
    )
    target_item: Mapped[KnowledgeItem] = relationship(
        "KnowledgeItem",
        foreign_keys=[target_item_id],
        back_populates="incoming_relationships",
    )


class KnowledgeSyncLog(BaseModel):
    __tablename__ = "knowledge_sync_logs"

    project_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        Text, default="running", nullable=False
    )  # "running", "completed", "failed"
    items_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    relationships_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
