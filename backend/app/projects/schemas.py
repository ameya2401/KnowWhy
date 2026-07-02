from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.project import ProjectRole, ProjectStatus, ProjectVisibility


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=1000)
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    status: ProjectStatus = ProjectStatus.ACTIVE
    color: str | None = Field(default=None, max_length=50)
    icon: str | None = Field(default=None, max_length=50)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    visibility: ProjectVisibility | None = None
    status: ProjectStatus | None = None
    color: str | None = Field(default=None, max_length=50)
    icon: str | None = Field(default=None, max_length=50)


class ProjectRead(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: str | None
    visibility: ProjectVisibility
    status: ProjectStatus
    color: str | None
    icon: str | None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectMemberRead(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime
    full_name: str
    email: EmailStr
    profile_picture_url: str | None


class ProjectListItem(BaseModel):
    project: ProjectRead
    role: ProjectRole


class ProjectMemberInvite(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.VIEWER


class ProjectMemberRoleUpdate(BaseModel):
    role: ProjectRole
