import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel

if TYPE_CHECKING:
    from app.models.organization import OrganizationMembership
    from app.models.user_session import UserSession


class AuthProvider(str, enum.Enum):
    GOOGLE = "google"
    GITHUB = "github"


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("provider", "provider_id", name="uq_users_provider_identity"),
    )

    email: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[AuthProvider] = mapped_column(
        Enum(
            AuthProvider, native_enum=False, values_callable=lambda enum_: [e.value for e in enum_]
        ),
        nullable=False,
    )
    provider_id: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_organization_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="OrganizationMembership.user_id",
    )
