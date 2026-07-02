# KnowWhy Architectural Decisions

## DEC-001: Use React SPA Foundation

Context: KnowWhy needs a frontend foundation that can support authenticated application screens without server rendering complexity.

Decision: Use React, TypeScript, Vite, Tailwind CSS, shadcn/ui-style primitives, React Router, TanStack Query, and Axios.

Reason: This matches the documented stack and keeps the MVP frontend simple and maintainable.

Tradeoffs: No SSR is provided, which is acceptable for the MVP application shell.

Files affected: `frontend/`

## DEC-002: Use FastAPI Modular Backend

Context: KnowWhy needs a backend foundation that can grow into service and repository layers.

Decision: Use FastAPI with separate API, auth, database, model, repository, service, dependency, and user packages.

Reason: This supports clean architecture without introducing microservice complexity.

Tradeoffs: Some package boundaries are intentionally light until future milestones add domain behavior.

Files affected: `backend/app/`

## DEC-003: Use Async SQLAlchemy and Alembic

Context: M02 requires production-ready database infrastructure.

Decision: Use SQLAlchemy 2.x async engine/session patterns and async Alembic migrations.

Reason: This keeps the backend ready for non-blocking FastAPI request handling.

Tradeoffs: Async database code is slightly more verbose than synchronous SQLAlchemy.

Files affected: `backend/app/database/`, `backend/alembic/`

## DEC-004: Use OAuth-First Authentication

Context: M03 explicitly forbids username/password authentication and requires Google/GitHub OAuth.

Decision: Accept provider OAuth access tokens from the frontend, verify them against Google/GitHub user-info APIs, then issue KnowWhy JWTs.

Reason: Provider verification keeps password handling out of KnowWhy while still giving the backend authoritative user identity records.

Tradeoffs: Local testing requires a real provider token or mocked provider verification.

Files affected: `backend/app/auth/`, `frontend/src/pages/LoginPage.tsx`

## DEC-005: Store Refresh Tokens as Hashed Sessions

Context: M03 requires session management, logout, refresh tokens, and secure token handling.

Decision: Store only SHA-256 refresh token hashes in `user_sessions`, send refresh tokens through HTTP-only cookies, and keep access tokens in frontend memory.

Reason: A database leak should not expose usable refresh tokens, and persistent browser storage is avoided for access tokens.

Tradeoffs: Refresh-token rotation requires database writes during refresh.

Files affected: `backend/app/models/user_session.py`, `backend/app/auth/`, `frontend/src/auth/`

## DEC-006: Organization/Workspace Isolation

Context: Multi-tenant workspace requirements in M04.

Decision: Create an `organizations` table representing tenant workspaces and `organization_memberships` managing user access roles (`owner`, `admin`, `member`). Every workspace is isolated and users can select their active workspace context in the frontend.

Reason: Simplifies tenant management and ensures data isolation using standard Postgres relational integrity.

Files affected: `backend/app/models/organization.py`, `frontend/src/organizations/`

## DEC-007: Project Scoping and Project-Level Permissions

Context: M05 requires projects to be associated with organizations and have customizable user permission roles.

Decision: Link projects to organizations and create a `project_members` mapping with custom roles (`owner`, `maintainer`, `contributor`, `viewer`). Ensure visibility settings and project archiving operate under owner-only roles.

Reason: Provides fine-grained control over project settings, member invites, and data security at the project-level.

Files affected: `backend/app/models/project.py`, `backend/app/projects/`, `frontend/src/projects/`, `frontend/src/pages/`
