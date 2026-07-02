from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.oauth import OAuthService
from app.auth.schemas import AuthTokenResponse
from app.auth.security import hash_token
from app.auth.tokens import token_service
from app.core.config import settings
from app.models.user import AuthProvider, User
from app.models.user_session import UserSession
from app.repositories.user_sessions import UserSessionRepository
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.oauth = OAuthService()
        self.users = UserRepository(session)
        self.sessions = UserSessionRepository(session)

    async def authenticate_oauth_with_refresh(
        self,
        provider: AuthProvider,
        provider_token: str,
    ) -> tuple[AuthTokenResponse, str]:
        profile = await self.oauth.verify_provider_token(provider, provider_token)
        user = await self.users.upsert_oauth_user(provider, profile)
        await self.session.commit()
        return await self.create_session_response(user)

    async def create_session_response(self, user: User) -> tuple[AuthTokenResponse, str]:
        refresh_token = token_service.create_refresh_token(user.id)
        user_session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days),
        )
        await self.sessions.create(user_session)
        await self.session.commit()

        return (
            AuthTokenResponse(
                access_token=token_service.create_access_token(user.id),
                expires_in=settings.jwt_access_token_expire_minutes * 60,
                user=user,
            ),
            refresh_token,
        )

    async def refresh_with_token(self, refresh_token: str | None) -> tuple[AuthTokenResponse, str]:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is required."
            )

        user_id = token_service.verify_token(refresh_token, expected_type="refresh")
        user_session = await self.sessions.get_active_by_refresh_hash(hash_token(refresh_token))
        if user_session is None or user_session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid."
            )

        user = await self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active."
            )

        await self.sessions.revoke(user_session)
        await self.session.commit()
        return await self.create_session_response(user)

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        user_session = await self.sessions.get_active_by_refresh_hash(hash_token(refresh_token))
        if user_session is not None:
            await self.sessions.revoke(user_session)
            await self.session.commit()
