from app.models.project import ProjectRole

ROLE_RANK: dict[ProjectRole, int] = {
    ProjectRole.VIEWER: 1,
    ProjectRole.CONTRIBUTOR: 2,
    ProjectRole.MAINTAINER: 3,
    ProjectRole.OWNER: 4,
}


def has_project_role_at_least(actual: ProjectRole, required: ProjectRole) -> bool:
    return ROLE_RANK[actual] >= ROLE_RANK[required]
