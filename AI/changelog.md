# KnowWhy Changelog

## 2026-07-03 - M10 KnowWhy Knowledge Engine

### Features Added

- Created `knowledge_items`, `knowledge_relationships`, and `knowledge_sync_logs` database tables with index and constraints.
- Added backend service layers `NormalizationEngine` and `KnowledgeService` converting raw GitHub, Notion, and Google Drive models to unified schema entities.
- Implemented automatic parent-child relationship generators (Notion parent links and Google Drive folder containment structure).
- Implemented regular expression hashtag matching (`#\d+`) to capture relationships from GitHub commits and pull requests referencing/fixing issues.
- Added API endpoints (`GET /api/knowledge`, `GET /api/knowledge/{id}`, `GET /api/knowledge/relationships/{id}`, `GET /api/knowledge/timeline`, and `POST /api/knowledge/sync`) to retrieve paginated stores, timelines, relationships, and trigger sync routines under role-based project protection.
- Added frontend TypeScript type definitions representing the knowledge items, relationships, and sync logs.
- Added frontend api methods (`listKnowledgeItems`, `getKnowledgeItem`, `getKnowledgeItemRelationships`, `getKnowledgeTimeline`, `syncKnowledge`) inside a dedicated API wrapper.
- Integrated a comprehensive "Knowledge Base" UI tab in `ProjectDetailPage.tsx` offering a searchable list view, source/type/status filtering, a vertical chronological timeline feed, manual sync controls, and an interactive side detail drawer/navigable relationship crawler.
- Fixed backend unit tests (32 passing total) validating the engine normalization mapping, relationship mappings, and API endpoints.

### Files Added

- Backend: `alembic/versions/20260703_0008_create_knowledge_tables.py`, `app/repositories/knowledge.py`, `app/services/knowledge.py`, `app/schemas/knowledge.py`, `app/api/routes/knowledge.py`, `tests/test_knowledge_engine.py`.
- Frontend: `src/types/knowledge.ts`, `src/services/knowledgeApi.ts`, `src/components/KnowledgeBrowser.tsx`.

### Files Modified

- Backend: `app/api/router.py`, `app/database/base.py`.
- Frontend: `src/pages/ProjectDetailPage.tsx`.
- Documentation: `AI/context.md`, `AI/progress.md`, `AI/decisions.md`, `AI/changelog.md`.

## 2026-07-02 - M09 Google Drive Integration

### Features Added

- Added `google_drive_files` table mapping to local database schema for Google Drive integration.
- Added backend `GoogleDriveAPIClient` supporting folder harvesting, hierarchy metadata crawls, and OAuth token exchange.
- Added backend Google Drive routes: `GET /integrations/google_drive`, `POST /integrations/google_drive/connect`, `POST /integrations/google_drive/sync`, `DELETE /integrations/google_drive/disconnect`.
- Added mock Google Drive OAuth token, directory indexing, and list API routes for offline integration testing.
- Added backend unit tests (30 passing total) covering credential encryption, folder indexing, file crawling, and metadata parsing.
- Added frontend integration services (`getGoogleDriveIntegration`, `connectGoogleDrive`, `syncGoogleDriveIntegration`, `disconnectGoogleDrive`).
- Added frontend Google Drive tab within `ProjectIntegrations.tsx` layout with connection status card, active status display, manual/mock connection form, sync control, search & mime-type filters, hierarchical breadcrumbs, and an interactive Folder Explorer.
- Added frontend Google Drive Callback page (`GoogleDriveCallbackPage.tsx`) and registered routing configuration.

### Files Added

- Backend: `app/api/routes/google_drive.py`, `app/integrations/google_drive.py`.
- Frontend: `src/pages/GoogleDriveCallbackPage.tsx`.

### Files Modified

- Backend: `app/models/integration.py`, `app/api/router.py`, `app/database/base.py`.
- Frontend: `src/services/integrationApi.ts`, `src/components/ProjectIntegrations.tsx`, `src/App.tsx`, `src/routes/router.tsx`.
- Documentation: `AI/context.md`, `AI/progress.md`, `AI/decisions.md`, `AI/changelog.md`.

## 2026-07-02 - M08 Notion Integration

### Features Added

- Added `notion_pages` table mapping to local database schema for Notion integration.
- Added backend `NotionAPIClient` supporting workspace searches and access token exchange.
- Added `NotionNormalizer` utility to map raw API responses to consistent title, author, and last-edited records.
- Added backend Notion routes: `GET /integrations/notion`, `POST /integrations/notion/connect`, `POST /integrations/notion/sync`, `DELETE /integrations/notion/disconnect`.
- Added mock Notion OAuth token and search API routes for offline integration testing.
- Added backend unit tests (25 passing total) covering credential encryption, item normalizer, workspace crawls, and incremental sync.
- Added frontend integration services (`getNotionIntegration`, `connectNotion`, `syncNotionIntegration`, `disconnectNotion`).
- Added frontend Notion tab within `ProjectIntegrations.tsx` layout with connection status, synced pages table list, manual sync control, and mock input forms.
- Added frontend Notion Callback page (`NotionCallbackPage.tsx`) and registered routing configuration.

## 2026-07-02 - M07 Workspace Dashboard

### Features Added

- Added backend `/integrations/github/dashboard` route returning sync data stats and chronological activity list.
- Added frontend `ProjectContext` and `ProjectProvider` to manage global active project selection, with persistence stored via `localStorage`.
- Added collapsible sidebar drawer layout featuring workspace & project switcher dropdown selects and a theme toggle.
- Added Dashboard Overview page (`DashboardPage.tsx`) displaying git integration status, sync triggers, metrics cards (commits, PRs, issues, contributors), recent activity list, quick actions, and empty states.
- Added dedicated Activity Page (`ActivityPage.tsx`) to display filterable recent workspace activity events.
- Fixed TypeScript declaration/mock interface mismatch across test files (`ProjectsPage.test.tsx`, `CreateProjectPage.test.tsx`, `DashboardPage.test.tsx`).
- Added robust, defensive optional-chaining lookups inside sidebar organization selectors to prevent runtime layout crash states.

### Files Added

- Frontend: `src/pages/ActivityPage.tsx`.

### Files Modified

- Frontend: `src/layouts/DashboardLayout.tsx`, `src/pages/DashboardPage.tsx`, `src/pages/DashboardPage.test.tsx`, `src/pages/ProjectsPage.test.tsx`, `src/pages/CreateProjectPage.test.tsx`, `src/routes/router.tsx`.
- Documentation: `AI/context.md`, `AI/progress.md`, `AI/decisions.md`, `AI/changelog.md`.

## 2026-07-02 - M06 External Integrations

### Features Added

- Added `integrations` table with AES-GCM credential encryption/decryption.
- Added `integration_repositories` table to map linked repos.
- Added `integration_commits`, `integration_pull_requests`, and `integration_issues` to store metadata of repository contents.
- Added backend GitHub OAuth connection routes: `GET /integrations/github`, `POST /integrations/github/connect`, `GET /integrations/github/repositories`, `POST /integrations/github/repositories/{github_repo_id}/connect`, `POST /integrations/github/sync`, `DELETE /integrations/github/disconnect`.
- Added mock external API endpoints in testing module to mock GitHub OAuth code exchange and repository listings.
- Added frontend Integrations tab in Project Details Page.
- Added frontend repository selection modal with search, select and multi-select capability.
- Added frontend sync dashboard with background sync polling and last synced metadata.
- Added frontend disconnect capability.
- Added frontend GitHub callback route (`/integrations/github/callback`) for OAuth flow processing.

### Files Added

- Frontend: `src/services/integrationApi.ts`, `src/components/ProjectIntegrations.tsx`, `src/pages/GitHubCallbackPage.tsx`.

### Files Modified

- Frontend: `src/pages/ProjectDetailPage.tsx`, `src/routes/router.tsx`.
- Documentation: `AI/context.md`, `AI/progress.md`, `AI/decisions.md`, `AI/changelog.md`.

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
