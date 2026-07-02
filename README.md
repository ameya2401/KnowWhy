# KnowWhy

KnowWhy is a production-grade Organizational Intelligence Platform. It is designed to become an intelligence layer across engineering and workplace tools, preserving organizational context and helping teams answer why decisions were made.

This repository currently contains the Milestone M02 foundation: frontend shell, backend health API, async database foundation, PostgreSQL and Redis connectivity, Docker orchestration, CI, and development tooling. Authentication, integrations, AI, search, RAG, and business workflows are intentionally not implemented yet.

## Architecture

KnowWhy uses a modular monolith foundation with clear boundaries:

- `frontend/` contains the React TypeScript application.
- `backend/` contains the FastAPI application.
- `database/` is reserved for database assets and migration-related documentation.
- `docker/` is reserved for container support files.
- `scripts/` contains local development helpers.
- `tests/` is reserved for cross-system tests.

Backend code follows a layered structure:

```text
API -> Services -> Repositories -> Database
```

The backend exposes `GET /health`, returning this response when PostgreSQL and Redis are reachable:

```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected"
}
```

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui-style components, React Router, TanStack Query, Axios
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, Uvicorn
- Database: PostgreSQL
- Cache: Redis
- Infrastructure: Docker, Docker Compose
- CI/CD: GitHub Actions

## Folder Structure

```text
KnowWhy/
├── AI/
├── Milestones/
├── ProjectOverview/
├── backend/
├── database/
├── docker/
├── docs/
├── frontend/
├── scripts/
├── tests/
├── .github/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Local Setup

Create environment variables from the example:

```bash
cp .env.example .env
```

Install backend dependencies:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
python -m pip install -r requirements-dev.txt
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Run database migrations when PostgreSQL is available:

```bash
alembic upgrade head
```

Verify PostgreSQL and Redis connectivity:

```bash
python scripts/check_dependencies.py
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run the frontend:

```bash
npm run dev
```

## Docker Commands

Start the full local stack:

```bash
docker compose up --build
```

Stop the stack:

```bash
docker compose down
```

Remove local service volumes:

```bash
docker compose down -v
```

## Development Workflow

Before opening a pull request:

```bash
cd frontend
npm run lint
npm run format:check
npm run test
npm run build
```

```bash
cd backend
python -m ruff check .
python -m ruff format --check .
python -m pytest
python -m compileall app tests
```

With Docker installed, verify the service stack:

```bash
docker compose up --build
curl http://localhost:8000/health
```

Inspect Alembic migration state:

```bash
docker compose exec backend alembic current
docker compose exec postgres psql -U knowwhy -d knowwhy -c "\dt"
```
