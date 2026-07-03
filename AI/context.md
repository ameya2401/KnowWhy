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

- **Milestone M06 External Integrations**:
  - `integrations` table linking external providers (e.g. `github`) to projects, with credentials encryption and status tracking (`connected`, `syncing`, `error`).
  - `integration_repositories` table storing metadata of linked repositories.
  - `integration_commits`, `integration_pull_requests`, and `integration_issues` tables to capture repository content metadata.
  - Backend integration service layer with secure AES-GCM credential encryption/decryption.
  - Mocked external APIs for GitHub OAuth and Repo listing to support reliable testing.
  - Frontend Integrations tab in Project Details Page showing connection status, repository selection modal (with search & multi-select), and sync controls.
  - Frontend GitHub OAuth Callback handler (`/integrations/github/callback`) to finalize authorization.

- **Milestone M07 Workspace Dashboard**:
  - Persistent frontend global selection context (`ProjectContext` and `ProjectProvider`) via `localStorage` to preserve selection state.
  - Collapsible sidebar drawer with nested navigations, theme toggler, and workspace switcher dropdowns.
  - Dashboard overview page displaying connected repository status, manual sync controls, and real Git integration details (aggregate metrics cards).
  - Chronological Recent Activity feed showing latest commits, pull requests, and issues.
  - Dedicated Activity Page with dropdown filtering by activity type.
  - Dynamic empty states for disconnected repositories and unconfigured projects.
  - Full TypeScript type-safety across components and mocks, and defensive organization-chaining lookups.
- **Milestone M08 Notion Integration**:
  - `notion_pages` table storing metadata of synced Notion workspace pages (title, author, parent structure, etc.).
  - Backend integration service layer with support for Notion API token exchange, page indexing, and incremental updates based on updated timestamps.
  - Frontend Notion Integration tab featuring connection status, list of synced Notion pages, sync controls, and background sync polling.
  - Frontend Notion OAuth Callback handler (`/integrations/notion/callback`) to finalize authorization.

- **Milestone M09 Google Drive Integration**:
  - `google_drive_files` table storing metadata of synced Google Drive files and directories (name, mime type, parent structure, file size, owner, url, modified timestamp).
  - Backend integration service layer with support for Google Drive API OAuth token exchange, file/folder metadata harvesting, hierarchy reconstruction, and background sync logic.
  - Frontend Google Drive Integration tab featuring connection status, sync controls, file size/type filters, search bar, hierarchical navigation breadcrumbs, and an interactive folder explorer.
  - Frontend Google Drive OAuth Callback handler (`/integrations/drive/callback`) to finalize authorization.

- **Milestone M10 KnowWhy Knowledge Engine**:
  - `knowledge_items`, `knowledge_relationships`, and `knowledge_sync_logs` tables in database schema.
  - Unified entity normalization engine (`NormalizationEngine` and `KnowledgeService`) supporting mapping, deduplication (upserts), and metadata parsing.
  - Automatic relationship mapping rules connecting Notion pages (parent hierarchy), Google Drive files (folder containment), and GitHub commits/PRs (issue reference parsing).
  - Backend Knowledge APIs supporting pagination, details retrieval, relationship fetching, and sync triggering with role-based project protection.
  - Backend pytest suite validating normalization, ingestion, and relationship synthesis.
  - Frontend TypeScript definitions and API client wrapper (`knowledgeApi.ts`).
  - Frontend "Knowledge Base" tab in Project Details Page providing list/timeline toggle views, status filtering, search bar, and an interactive side drawer for entity details and relationship navigation.

