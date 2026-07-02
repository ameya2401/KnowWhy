# KnowWhy Implementation Context

Last Updated: 2026-07-02

## Current Implementation State

Milestone M05 Projects is implemented.

KnowWhy currently contains:

- React + TypeScript + Vite frontend in `frontend/`
- Tailwind CSS and shadcn/ui-style UI primitives
- Frontend login page with Google and GitHub OAuth token submission for local OAuth verification
- Frontend protected route wrapper that routes unauthenticated users to `/login`
- In-memory frontend access token handling with refresh through backend HTTP-only cookie
- FastAPI backend in `backend/`
- Async SQLAlchemy database foundation with Declarative Base and reusable abstract BaseModel
- Alembic async migration environment with versioned migrations
- `users` table for OAuth identities
- `user_sessions` table for hashed refresh-token sessions
- Google and GitHub OAuth provider-token verification
- JWT access and refresh token creation and verification
- HTTP-only refresh cookie support
- `POST /auth/google`
- `POST /auth/github`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /users/me`
- Reusable `get_current_user` protected-route dependency
- `GET /health` endpoint reporting API, PostgreSQL, and Redis status
- Dockerfiles, Docker Compose, and GitHub Actions CI

- **Milestone M04 Multi-Tenant Workspaces**:
  - `organizations` table for multi-tenant workspace isolation.
  - `organization_memberships` table for member roles (`owner`, `member`, `admin`).
  - Backend Organization CRUD routes, workspace selection, and invite system.
  - Frontend Organization Selection, Creation, and Settings management pages.
  
- **Milestone M05 Projects**:
  - `projects` table for projects, grouped under organizations, with visibility (`public`, `private`) and status (`active`, `archived`).
  - `project_members` table linking users to projects with roles (`owner`, `maintainer`, `contributor`, `viewer`).
  - Backend Project API routes for list, create, details, settings, archive, member invite, role updates, and member removal.
  - Frontend Projects list dashboard with search, visibility & status filters.
  - Frontend Create Project page, Project Detail page with overview/members tabs, and Project Settings page with Danger Zone.
