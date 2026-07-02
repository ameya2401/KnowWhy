from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


class TokenService:
    def create_access_token(self, user_id: UUID) -> str:
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        return self._encode_token(subject=user_id, token_type="access", expires_at=expires_at)

    def create_refresh_token(self, user_id: UUID) -> str:
        expires_at = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
        return self._encode_token(subject=user_id, token_type="refresh", expires_at=expires_at)

    def verify_token(self, token: str, expected_type: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"require": ["exp", "sub", "typ", "jti"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
            ) from exc

        if payload.get("typ") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type."
            )

        try:
            return UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject."
            ) from exc

    def _encode_token(self, subject: UUID, token_type: str, expires_at: datetime) -> str:
        payload = {
            "sub": str(subject),
            "typ": token_type,
            "jti": str(uuid4()),
            "iat": datetime.now(UTC),
            "exp": expires_at,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


token_service = TokenService()
