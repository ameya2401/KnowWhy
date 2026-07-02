# KnowWhy Changelog

## 2026-07-02 - M02 Database Foundation

### Features Added

- Added dedicated async database package.
- Added SQLAlchemy Declarative Base.
- Added reusable abstract BaseModel with UUID primary key and automatic timestamps.
- Added async SQLAlchemy engine and async session factory.
- Added FastAPI database session dependency.
- Added PostgreSQL health check utility.
- Added Redis health check utility.
- Added configurable startup validation for external services.
- Updated `/health` to report API, database, and Redis status.
- Configured Alembic for async migrations and Base metadata autogeneration.
- Added initial Alembic database foundation migration.
- Added migration and dependency-check commands to README.
- Added M02 settings to `.env.example` and Docker Compose.

### Files Added

- `backend/app/database/__init__.py`
- `backend/app/database/base.py`
- `backend/app/database/health.py`
- `backend/app/database/session.py`
- `backend/app/database/startup.py`
- `backend/alembic/versions/20260702_0001_database_foundation.py`
- `frontend/.prettierignore`

### Files Modified

- `.env.example`
- `README.md`
- `docker-compose.yml`
- `backend/alembic/env.py`
- `backend/app/api/routes/health.py`
- `backend/app/core/cache.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/main.py`
- `backend/app/schemas/health.py`
- `backend/scripts/check_dependencies.py`
- `backend/tests/test_health.py`
- `AI/context.md`
- `AI/progress.md`
- `AI/decisions.md`
- `AI/changelog.md`

### Bug Fixes

- Prevented dependency health failures from surfacing as unstructured 500 responses.
- Excluded generated frontend build output from Prettier checks.

### Breaking Changes

- `/health` response shape changed from `{"status":"ok"}` to include `database` and `redis` fields.

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
