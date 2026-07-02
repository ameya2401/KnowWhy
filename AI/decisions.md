# KnowWhy Architectural Decisions

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
