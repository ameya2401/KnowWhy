from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession


class UserSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_session: UserSession) -> UserSession:
        self.session.add(user_session)
        await self.session.flush()
        return user_session

    async def get_active_by_refresh_hash(self, refresh_token_hash: str) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash == refresh_token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > datetime.now(UTC),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, user_session: UserSession) -> None:
        user_session.revoked_at = datetime.now(UTC)
        await self.session.flush()
