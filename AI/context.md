# KnowWhy Implementation Context

Last Updated: 2026-07-02

## Current Implementation State

Milestone M01 Project Foundation is implemented.

KnowWhy currently contains a production-oriented foundation only:

- React + TypeScript + Vite frontend in `frontend/`
- Tailwind CSS and shadcn/ui-style primitives for UI composition
- React Router configured with a dashboard placeholder route
- TanStack Query configured for future server state
- Axios API client configured through `VITE_API_BASE_URL`
- FastAPI backend in `backend/`
- Layered backend folders for `api`, `core`, `models`, `schemas`, `repositories`, and `services`
- `GET /health` endpoint returning `{"status":"ok"}`
- SQLAlchemy async engine configuration for PostgreSQL connectivity
- Redis async client configuration for cache connectivity
- Alembic initialized without application tables
- Dockerfiles for frontend and backend
- `docker-compose.yml` for frontend, backend, PostgreSQL, and Redis
- GitHub Actions CI for frontend and backend validation
- `.env.example` documenting required environment variables
- README with architecture, setup, Docker commands, and development workflow

No authentication, organizations, integrations, AI, search, RAG, or business logic has been implemented.
