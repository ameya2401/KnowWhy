# KnowWhy Changelog

## 2026-07-02 - M01 Project Foundation

### Features Added

- Initialized React + TypeScript + Vite frontend.
- Configured Tailwind CSS and shadcn/ui-style component primitives.
- Added React Router with a professional dashboard placeholder page.
- Added TanStack Query client setup.
- Added Axios API client setup.
- Initialized FastAPI backend.
- Added `GET /health` endpoint returning `{"status":"ok"}`.
- Added PostgreSQL connection configuration through SQLAlchemy async engine.
- Added Redis connection configuration through async Redis client.
- Added Alembic foundation without application tables.
- Added Dockerfiles for frontend and backend.
- Added Docker Compose services for frontend, backend, PostgreSQL, and Redis.
- Added GitHub Actions CI for frontend and backend validation.
- Added root `.env.example`.
- Added professional README with overview, architecture, setup, Docker commands, and workflow.

### Files Added

- `.github/workflows/ci.yml`
- `.env.example`
- `.gitignore`
- `README.md`
- `docker-compose.yml`
- `backend/`
- `frontend/`
- `database/.gitkeep`
- `docker/.gitkeep`
- `docs/.gitkeep`
- `scripts/.gitkeep`
- `tests/.gitkeep`

### Files Modified

- `AI/context.md`
- `AI/progress.md`
- `AI/decisions.md`
- `AI/changelog.md`

### Bug Fixes

- Resolved frontend TypeScript configuration issues for Vite and Vitest.
- Resolved backend Ruff import-order issue.
- Upgraded audited frontend packages to remove npm vulnerabilities.

### Breaking Changes

- None.
