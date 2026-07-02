from fastapi import APIRouter

from app.api.routes.github import router as github_router
from app.api.routes.health import router as health_router
from app.auth.router import router as auth_router
from app.organizations.router import router as organizations_router
from app.projects.router import router as projects_router
from app.users.router import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(projects_router)
api_router.include_router(users_router)
api_router.include_router(github_router)

