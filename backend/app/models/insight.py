from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class EngineeringInsight(BaseModel):
    __tablename__ = "engineering_insights"

    project_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    # "documentation_gap", "stale_knowledge", "architecture_drift", "duplicate_knowledge", "project_health", "knowledge_coverage"  # noqa: E501
    severity: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    # "critical", "warning", "suggestion"
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # List of items/evidence. Format: [{"id": "...", "title": "...", "type": "...", "url": "..."}]
    suggested_actions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="active", index=True, nullable=False)
    # "active", "resolved", "dismissed"
    metadata_json: Mapped[dict | None] = mapped_column(JSON, name="metadata", nullable=True)

    project: Mapped["Project"] = relationship("Project", lazy="raise")  # noqa: F821
    organization: Mapped["Organization"] = relationship("Organization", lazy="raise")  # noqa: F821
