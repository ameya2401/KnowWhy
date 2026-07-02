from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.oauth import OAuthUserInfo
from app.models.user import AuthProvider, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_provider_identity(
        self,
        provider: AuthProvider,
        provider_id: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.provider == provider, User.provider_id == provider_id)
        )
        return result.scalar_one_or_none()

    async def upsert_oauth_user(self, provider: AuthProvider, profile: OAuthUserInfo) -> User:
        existing = await self.get_by_provider_identity(provider, profile.provider_id)
        now = datetime.now(UTC)

        if existing is not None:
            existing.email = profile.email
            existing.full_name = profile.full_name
            existing.profile_picture_url = profile.profile_picture_url
            existing.last_login_at = now
            await self.session.flush()
            return existing

        user = User(
            email=profile.email,
            full_name=profile.full_name,
            profile_picture_url=profile.profile_picture_url,
            provider=provider,
            provider_id=profile.provider_id,
            last_login_at=now,
        )
        self.session.add(user)
        await self.session.flush()
        return user
