# KnowWhy Changelog

## 2026-07-02 - M05 Projects

### Features Added

- Added projects model with visibility (`public`, `private`) and status (`active`, `archived`) fields.
- Added project members model with roles (`owner`, `maintainer`, `contributor`, `viewer`).
- Added backend project API routes for listing, creating, retrieving, updating, and deleting projects.
- Added project archiving and membership invitation API endpoints.
- Added project-level permissions checks for settings access, invites, role updates, and deletions.
- Added frontend projects dashboard page with search and visibility/status filters.
- Added frontend Create Project page.
- Added frontend Project Detail page with Overview and Members tabs.
- Added frontend Project Settings page with Danger Zone configuration (slug validation for delete).
- Added frontend navigation sidebar link to Projects page.
- Added frontend Vitest coverage and backend pytest test suite for projects.

### Files Added

- Backend: `app/projects/router.py`, `app/projects/schemas.py`, `app/projects/service.py`, `app/repositories/projects.py`, `app/models/project.py`.
- Frontend: `src/pages/ProjectsPage.tsx`, `src/pages/ProjectsPage.test.tsx`, `src/pages/CreateProjectPage.tsx`, `src/pages/CreateProjectPage.test.tsx`, `src/pages/ProjectDetailPage.tsx`, `src/pages/ProjectSettingsPage.tsx`, `src/projects/projectApi.ts`, `src/projects/types.ts`.

### Bug Fixes

- Fixed card sub-element imports and added missing `destructive` button variant in frontend primitives.
- Fixed TypeScript compiler errors, implicit `any` assignments, and unused variables.

## 2026-07-02 - M04 Multi-Tenant Workspaces

### Features Added

- Added organization model for tenant workspaces.
- Added organization memberships model with owner/admin/member roles.
- Added workspace selection, creation, and invite routing on frontend and backend.

## 2026-07-02 - M03 Authentication & Identity

### Features Added

- Added OAuth-first user identity model.
- Added user session model for hashed refresh tokens.
- Added Google provider-token verification.
- Added GitHub provider-token verification.
- Added JWT access and refresh token service.
- Added HTTP-only refresh cookie helpers.
- Added login, refresh, logout, and current-user API routes.
- Added reusable protected-route dependency for backend endpoints.
- Added frontend login page for Google and GitHub.
- Added frontend protected route wrapper.
- Added frontend auth context with refresh-session restoration.
- Added Alembic migration for `users` and `user_sessions`.

### Files Added

- Backend auth, users, dependencies, models, repositories, tests, and migrations.
- Frontend auth context, protected route, login page, dashboard shell, tests, and app configuration.
- Root Docker, README, environment example, and CI source files.

### Files Modified

- `AI/context.md`
- `AI/progress.md`
- `AI/decisions.md`
- `AI/changelog.md`

### Bug Fixes

- Restored missing source files from prior foundation milestones.
- Avoided persistent browser storage for access tokens.
- Ensured dependency health failures return structured responses.

### Breaking Changes

- `/health` includes `database` and `redis` fields.
