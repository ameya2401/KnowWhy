# KnowWhy Implementation Context

Last Updated: 2026-07-02

## Current Implementation State

Milestone M02 Database Foundation is implemented.

KnowWhy currently contains a production-oriented foundation only:

- React + TypeScript + Vite frontend in `frontend/`
- Tailwind CSS and shadcn/ui-style primitives for UI composition
- React Router configured with a dashboard placeholder route
- TanStack Query configured for future server state
- Axios API client configured through `VITE_API_BASE_URL`
- FastAPI backend in `backend/`
- Layered backend folders for `api`, `core`, `models`, `schemas`, `repositories`, and `services`
- `GET /health` endpoint returning dependency status for the API, PostgreSQL, and Redis
- Dedicated `app/database` package with SQLAlchemy 2.x async engine and async session factory
- Declarative SQLAlchemy Base and reusable abstract BaseModel with UUID `id`, `created_at`, and `updated_at`
- FastAPI database session dependency
- PostgreSQL health check with controlled degraded response on connection failure
- Redis health check with controlled degraded response on connection failure
- Configurable startup validation for PostgreSQL and Redis through `VALIDATE_EXTERNAL_SERVICES_ON_STARTUP`
- Alembic configured with async migration environment, Base metadata, versioning support, and initial no-op database foundation migration
- Dockerfiles for frontend and backend
- `docker-compose.yml` for frontend, backend, PostgreSQL, and Redis
- GitHub Actions CI for frontend and backend validation
- `.env.example` documenting required environment variables
- README with architecture, setup, Docker commands, and development workflow

No authentication, organizations, integrations, AI, search, RAG, or business logic has been implemented.
