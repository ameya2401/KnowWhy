from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.organization import OrganizationRole


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=2, max_length=80)
    logo_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=1000)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    logo_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=1000)


class OrganizationRead(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: str | None
    description: str | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationMembershipRead(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationRole
    joined_at: datetime
    full_name: str
    email: EmailStr
    profile_picture_url: str | None


class OrganizationListItem(BaseModel):
    organization: OrganizationRead
    role: OrganizationRole


class InvitationCreate(BaseModel):
    email: EmailStr
    role: OrganizationRole = OrganizationRole.MEMBER


class InvitationRead(BaseModel):
    id: UUID
    organization_id: UUID
    email: EmailStr
    role: OrganizationRole
    invited_by_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipRoleUpdate(BaseModel):
    role: OrganizationRole


class ActiveOrganizationUpdate(BaseModel):
    organization_id: UUID


class ActiveOrganizationRead(BaseModel):
    organization: OrganizationRead | None
    role: OrganizationRole | None
