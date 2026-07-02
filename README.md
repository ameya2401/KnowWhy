# KnowWhy

KnowWhy is an Organizational Intelligence Platform. This repository currently contains the foundation through Milestone M03: project structure, async database layer, OAuth-first authentication, JWT session management, and a React login/dashboard shell.

Authentication is implemented without username/password login. Google and GitHub provider tokens are verified server-side before KnowWhy issues signed access and refresh tokens.

## Local Development

Backend:

```bash
cd backend
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Docker:

```bash
docker compose up --build
```

Migrations:

```bash
cd backend
python -m alembic upgrade head
```

Validation:

```bash
cd backend
python -m ruff check .
python -m ruff format --check .
python -m pytest
python -m compileall app tests alembic
```

```bash
cd frontend
npm run lint
npm run format:check
npm run test
npm run build
```
