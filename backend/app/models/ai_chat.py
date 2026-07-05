from uuid import UUID
from sqlalchemy import Text, ForeignKey, JSON, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import BaseModel


class AIConversation(BaseModel):
    __tablename__ = "ai_conversations"

    project_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)

    # Configuration overrides
    provider: Mapped[str] = mapped_column(Text, default="openai", nullable=False)
    model: Mapped[str | None] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    citation_mode: Mapped[str] = mapped_column(Text, default="grounded", nullable=False)
    streaming_on: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AIMessage(BaseModel):
    __tablename__ = "ai_messages"

    conversation_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Stores latency, confidence, citations, follow-up suggestions, etc.
    metadata_json: Mapped[dict | None] = mapped_column(JSON, name="metadata", nullable=True)

    conversation: Mapped[AIConversation] = relationship(back_populates="messages")
