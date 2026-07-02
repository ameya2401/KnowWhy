from app.models.organization import OrganizationRole

ROLE_RANK: dict[OrganizationRole, int] = {
    OrganizationRole.MEMBER: 1,
    OrganizationRole.ADMIN: 2,
    OrganizationRole.OWNER: 3,
}


def has_role_at_least(actual: OrganizationRole, required: OrganizationRole) -> bool:
    return ROLE_RANK[actual] >= ROLE_RANK[required]
