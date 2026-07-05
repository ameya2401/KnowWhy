from fastapi import APIRouter

from app.api.routes.ai import router as ai_router
from app.api.routes.drive import router as drive_router
from app.api.routes.embeddings import router as embeddings_router
from app.api.routes.github import router as github_router
from app.api.routes.graph import router as graph_router
from app.api.routes.health import router as health_router
from app.api.routes.insight import router as insight_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.notion import router as notion_router
from app.api.routes.search import router as search_router
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
api_router.include_router(notion_router)
api_router.include_router(drive_router)
api_router.include_router(knowledge_router)
api_router.include_router(search_router)
api_router.include_router(embeddings_router)
api_router.include_router(ai_router)
api_router.include_router(graph_router)
api_router.include_router(insight_router)
