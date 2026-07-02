from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import AuthProvider


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    profile_picture_url: str | None
    provider: AuthProvider
    is_active: bool
    last_login_at: datetime | None
    active_organization_id: UUID | None

    model_config = {"from_attributes": True}
