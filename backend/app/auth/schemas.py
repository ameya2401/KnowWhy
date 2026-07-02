from pydantic import BaseModel, Field

from app.users.schemas import UserRead


class OAuthTokenRequest(BaseModel):
    access_token: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead
