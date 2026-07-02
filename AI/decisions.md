# KnowWhy Architectural Decisions

## DEC-006: Add Dedicated Async Database Package

Context: M02 requires a production-ready database foundation using modern SQLAlchemy 2.x patterns.

Decision: Added `backend/app/database/` with Declarative Base, abstract BaseModel, async engine, async session factory, FastAPI session dependency, health checks, and startup validation.

Reason: Keeping database infrastructure in its own package gives future repositories and services one consistent place to depend on SQLAlchemy primitives.

Tradeoffs: The existing `app/core/database.py` remains as a compatibility facade to avoid unnecessary churn from M01.

Files affected: `backend/app/database/`, `backend/app/core/database.py`

## DEC-007: Use UUID and Timestamp Fields in Abstract BaseModel Only

Context: M02 requires a reusable BaseModel but forbids application business models.

Decision: Implemented an abstract `BaseModel` with UUID `id`, timezone-aware `created_at`, and timezone-aware `updated_at`, but did not create any concrete domain tables.

Reason: Future domain models can inherit common fields without M02 prematurely introducing users, organizations, or other business entities.

Tradeoffs: The initial Alembic migration is intentionally a no-op except versioning because no concrete tables exist yet.

Files affected: `backend/app/database/base.py`, `backend/alembic/versions/20260702_0001_database_foundation.py`

## DEC-008: Make External Service Startup Validation Configurable

Context: M02 requires startup validation while local tests and source builds should not require live PostgreSQL and Redis processes.

Decision: Added `VALIDATE_EXTERNAL_SERVICES_ON_STARTUP`, disabled by default and enabled in Docker Compose.

Reason: Docker and production-like environments can fail fast when PostgreSQL or Redis are unavailable, while unit tests and local source checks remain deterministic.

Tradeoffs: Developers running the backend outside Docker must opt into startup validation explicitly if they want fail-fast behavior.

Files affected: `backend/app/core/config.py`, `backend/app/main.py`, `docker-compose.yml`, `.env.example`

## DEC-009: Return Structured Degraded Health Responses

Context: M02 requires `/health` to report database and Redis connectivity.

Decision: `/health` returns `200` with connected statuses when dependencies are reachable and `503` with `degraded` statuses when one or both dependencies are unavailable.

Reason: A dependency outage should be machine-readable without exposing internal exceptions or returning an unstructured server error.

Tradeoffs: Local environments without PostgreSQL or Redis receive `503` until services are started.

Files affected: `backend/app/api/routes/health.py`, `backend/app/schemas/health.py`, `backend/app/database/health.py`

## DEC-001: Initialize Frontend as React SPA

Context: M01 requires a frontend foundation using React, TypeScript, Vite, Tailwind CSS, shadcn/ui, React Router, TanStack Query, and Axios.

Decision: Implemented the frontend as a Vite-powered React SPA with TypeScript, React Router, TanStack Query, Axios, Tailwind CSS, and local shadcn/ui-style primitives.

Reason: This matches the documented MVP stack while keeping the foundation simple and replaceable.

Tradeoffs: The dashboard is intentionally a shell, so no real product workflows exist yet. This avoids implementing future milestone behavior early.

Files affected: `frontend/`

## DEC-002: Initialize Backend as FastAPI Modular Monolith

Context: M01 requires FastAPI with clean folder boundaries and a health endpoint.

Decision: Implemented a FastAPI application with `api`, `core`, `models`, `schemas`, `repositories`, and `services` packages and a minimal `GET /health` endpoint.

Reason: The structure supports clean architecture and future service/repository boundaries without introducing premature business logic.

Tradeoffs: Some folders are intentionally empty except package markers because M01 does not define domain models or services yet.

Files affected: `backend/app/`

## DEC-003: Configure PostgreSQL and Redis Without Application Tables

Context: M01 requires PostgreSQL and Redis connectivity but explicitly forbids application tables and business logic.

Decision: Added SQLAlchemy async engine setup, Redis async client setup, and a dependency check script without creating application models or migrations.

Reason: Connectivity is verifiable while respecting the milestone boundary.

Tradeoffs: Runtime dependency checks require PostgreSQL and Redis services to be running, typically through Docker Compose.

Files affected: `backend/app/core/database.py`, `backend/app/core/cache.py`, `backend/scripts/check_dependencies.py`, `backend/alembic/`

## DEC-004: Use Docker Compose for the Local Foundation Stack

Context: M01 requires frontend, backend, PostgreSQL, and Redis services to start together.

Decision: Added service Dockerfiles and a root `docker-compose.yml` with health checks for PostgreSQL and Redis.

Reason: Docker Compose provides a repeatable local environment for the MVP foundation.

Tradeoffs: Docker could not be executed in the current environment because the Docker CLI is unavailable.

Files affected: `docker-compose.yml`, `frontend/Dockerfile`, `backend/Dockerfile`

## DEC-005: Add CI Validation Before Deployment Exists

Context: M01 requires GitHub Actions that install dependencies, build frontend/backend, and run tests with no deployment.

Decision: Added a CI workflow with separate frontend and backend jobs for linting, formatting checks, tests, and builds/compile checks.

Reason: This keeps milestone verification repeatable and prevents deployment concerns from entering M01.

Tradeoffs: CI assumes lockfiles and dependency manifests remain current.

Files affected: `.github/workflows/ci.yml`
