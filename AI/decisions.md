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

## DEC-008: External Integrations Scoping and Credentials Encryption

Context: M06 requires integrating projects with third-party service providers (specifically GitHub) and storing sensitive OAuth credentials securely.

Decision:
1. Scope integrations and linked repositories directly to projects to ensure tenant isolation.
2. Encrypt integration credentials using AES-GCM with a 256-bit key derived from a backend secret key.
3. Decrypt credentials on demand during background synchronization tasks.
4. Support mock/manual token configuration in the frontend to facilitate testing without requiring live OAuth flows.

Reason: Protects sensitive API credentials in the database while giving users flexible access control per project and enabling seamless testability.

Files affected: `backend/app/integrations/`, `frontend/src/services/integrationApi.ts`, `frontend/src/components/ProjectIntegrations.tsx`

## DEC-009: Global Project Selection Context and Persistent Workspace State

Context: M07 requires a cohesive navigation experience across projects and workspaces, where selecting a project updates all dashboard views (overview stats, recent activity, integration detail).

Decision:
1. Implement a global `ProjectProvider` and `ProjectContext` wrapping the workspace application shell.
2. Persist the active project selection inside browser `localStorage` under a workspace-scoped key, so reloading the page or switching tabs retains the user's active focus.
3. Apply defensive, optional-chaining lookups (`activeOrganization?.organization?.id`) inside sidebar components to prevent rendering and hydration crash cycles if organizations load asynchronously.

Reason: Keeps dashboard routing decoupled from path prefixes while preserving a seamless user workspace state across sessions.

Files affected: `frontend/src/projects/ProjectContext.ts`, `frontend/src/projects/ProjectProvider.tsx`, `frontend/src/layouts/DashboardLayout.tsx`

## DEC-010: Notion Integration Architecture and Workspace Indexing

Context: M08 requires synchronizing Notion workspace documentation, databases, and subpages securely per project context, while handling incremental indexing based on updated timestamps.

Decision:
1. Store page metadata locally in a dedicated `notion_pages` table, establishing unique constraint on `(integration_id, notion_page_id)` to handle update-upserts cleanly.
2. Implement incremental syncing: check database for existing records, comparing the incoming Notion page `last_edited_time` against the local record. Only write to DB if the incoming edit is newer.
3. Design a normalized parsing structure (`NotionNormalizer`) mapping rich/nested titles, author data, and URL layouts safely.
4. Establish `/integrations/notion/callback` OAuth callback handling, storing securely encrypted tokens.

Reason: Protects workspace documentation metadata, reduces indexing overhead via timestamps, and maintains full tenant isolation.

Files affected: `backend/app/models/integration.py`, `backend/app/integrations/`, `backend/app/api/routes/notion.py`, `frontend/src/components/ProjectIntegrations.tsx`

## DEC-011: Google Drive Integration Architecture and Interactive Folder Explorer

Context: M09 requires synchronizing Google Drive documents (spreadsheets, text documents, folders, and PDFs) securely per project context, while handling hierarchical navigation of files in the frontend.

Decision:
1. Store file and directory metadata locally in a dedicated `google_drive_files` table, establishing unique constraint on `(integration_id, google_file_id)` to handle update-upserts cleanly.
2. Implement backend sync logic harvesting Google Drive API metadata (parents, size, webViewLink, etc.) and storing tokens securely encrypted.
3. Design a hierarchical navigation interface in the React frontend: calculate parent paths dynamically via breadcrumb traversal in local state, filter by mime type presets, and support folder clicking to drill down.
4. Establish `/integrations/drive/callback` OAuth callback handling, storing securely encrypted tokens.

Reason: Reduces page indexing and harvesting overhead, keeps navigation snappy via browser-side folder hierarchies, and maintains full tenant isolation.

Files affected: `backend/app/models/integration.py`, `backend/app/integrations/`, `backend/app/api/routes/google_drive.py`, `frontend/src/components/ProjectIntegrations.tsx`

## DEC-012: Unified Knowledge Engine, Graph Relationships and Knowledge Base UI

Context: M10 requires a central, source-agnostic knowledge storage format to unify and index data from all connected integrations, auto-generating relationship edges (Notion hierarchy, Google Drive folders, GitHub issue references) and exposing these inside an interactive browse UI.

Decision:
1. Create a `knowledge_items` table representing unified resources, an indexable `uq_knowledge_items_project_source_entity` constraint for idempotent updates, a `knowledge_relationships` table for directional relationship edges, and `knowledge_sync_logs` for audit metrics.
2. Normalize structures on the fly with a modular `NormalizationEngine` converting provider-specific models (commits, PRs, issues, Notion pages, Google Drive files/directories) into unified knowledge items.
3. Generate relationship mappings dynamically: parse Notion/Google Drive parent folders, scan commit logs for issue numbers (`#\d+`), and scan pull request descriptions for closing target tags (`#\d+`).
4. Build a comprehensive "Knowledge Base" UI tab containing a search input, status/source filters, a timeline view feed, and a detailed sidebar/drawer permitting cross-navigation through the relationship links.

Reason: Decouples the application's search and AI layers from integration-specific models, minimizes synchronization overhead via idempotent database upserts, and improves navigate-ability through relational link crawling.

Files affected: `backend/app/models/knowledge.py`, `backend/app/repositories/knowledge.py`, `backend/app/services/knowledge.py`, `backend/app/api/routes/knowledge.py`, `frontend/src/types/knowledge.ts`, `frontend/src/services/knowledgeApi.ts`, `frontend/src/components/KnowledgeBrowser.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`

## DEC-013: Frontend Search Interface with Autocomplete and Highlighting

Context: M11 requires a search engine page with advanced filters, autocomplete queries, match highlights, score metrics, and details/relationships drawer.

Decision:
1. Implement `SearchPage.tsx` under protected `/search` routing.
2. Build an autocomplete dropdown displaying prefix recommendations and cached recent search history.
3. Design a side filter bar dynamically rendering available sources, entity types, authors, and tag pills queried from the backend, along with sorting and date inputs.
4. Highlight keyword match occurrences within titles and descriptions using dynamically rendered `<mark>` splits.
5. Reuse side drawer panels allowing traversal of graph relationship links directly.
6. Install a global header search bar in `DashboardLayout.tsx` and hook keydown `/` shortcut handlers.

Reason: Increases discoverability of index items, speeds up query iterations with local filter refinement, and maintains layout consistency with standard design design-system properties.

Files affected: `frontend/src/pages/SearchPage.tsx`, `frontend/src/routes/router.tsx`, `frontend/src/layouts/DashboardLayout.tsx`

## DEC-014: Semantic Chunking, Asynchronous Indexing State Machine, and Indexing Control Panel

Context: M12 requires a background embedding pipeline to parse knowledge items, generate vector chunks, compute embedding matrices, track execution state (start, pause, resume, reindex), and report queue metrics in the UI.

Decision:
1. Create a `knowledge_chunks` database model containing text segments, token counters, character index boundaries, and 1536-dimensional L2 normalized embeddings.
2. Implement a background state machine `EmbeddingQueueService` managing `ProjectQueueState` instances. Use Python `asyncio.create_task` to run queue workers in the background, permitting clean cancellation (pause) and resuming.
3. Expose REST API routes under `/embeddings` for start, pause, resume, reindex, status, and statistics.
4. Integrate a "Semantic Indexing" tab in the frontend Project Details Page, featuring control room buttons, progress bars, queue sizes, and vector DB metrics.

Reason: Decouples heavy vector computation from client request-response cycles, provides precise control over background processes, and offers immediate visual diagnostic status.

Files affected: `backend/app/models/knowledge.py`, `backend/app/services/embeddings.py`, `backend/app/services/embedding_queue.py`, `backend/app/api/routes/embeddings.py`, `frontend/src/components/EmbeddingControls.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`

## DEC-015: Hybrid Search Engine and Rank Fusion (RRF)

Context: Neither lexical search nor semantic vector search alone yields comprehensive organizational search results. Lexical matches technical keywords perfectly, while semantic matches general meaning. M13 requires a unified Hybrid Retrieval Engine combining both.

Decision:
1. Create a `SearchService` method `hybrid_search` combining keyword-based lexical results and pgvector-based semantic results.
2. Implement Reciprocal Rank Fusion (RRF) as the default rank fusion technique, computing RRF scores to merge results without duplicates.
3. Apply a custom weighted re-ranking formula considering lexical scores, semantic similarities, source reliability, and document updated recency.
4. Expose REST endpoints under `/search`: `GET /hybrid` (search), `GET /explain/{item_id}` (explanation), and `GET /statistics` (diagnostics).
5. Build a premium UI with a toggle switch, search explanation panel, and diagnostics view in the frontend Search tab.

Reason: Merges lexical precision with semantic context, handles duplicate result filters, details search explainability, and satisfies strict permission-aware project/organization isolation.

Files affected: `backend/app/api/routes/search.py`, `backend/app/services/search.py`, `frontend/src/pages/SearchPage.tsx`

## DEC-016: AI Intelligence Engine and Developer Debug Dashboard

Context: M14 requires building the final AI Intelligence Engine layer containing custom system instruction generation, context token budgeting, query intent categorization, citation mapping, and multi-provider swapping, and displaying these in an AI Debug Dashboard for developers.

Decision:
1. Implement a pipeline including `QueryProcessor` (intent keyword parser), `ContextBuilder` (deduplicating items and fitting within custom token budgets), `PromptBuilder` (formatting RAG prompts), and `CitationEngine` (mapping cited files/sources).
2. Design a pluggable `LLMProvider` interface with active provider settings, supporting real OpenAI/Anthropic/Gemini API verification and simulated fallback.
3. Build a dedicated "Intelligence Engine" dashboard tab within Project Details Page containing configuration controls, API key indicators, dual-mode RAG sandbox tester (Q&A/Explain), and performance telemetry panels (latency timers, confidence values, source lists).

Reason: Provides full developer visibility into RAG pipeline operations, prompt limits, token consumption, and response performance without the complexity of chat UI integration.

Files affected: `backend/app/services/ai.py`, `backend/app/api/routes/ai.py`, `frontend/src/components/AIDebugDashboard.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`

## DEC-017: Conversational AI Assistant Integration and Real-Time Token Streaming

Context: M15 requires a premium, interactive, real-time conversational AI chat interface with settings side panels, conversation logs, suggested queries, streaming SSE response chunks, confidence telemetry, and citation explorer widgets.

Decision:
1. Implement a conversational data schema `ai_conversations` and `ai_messages` linked to projects and users, managing custom model configurations (provider, temperature, streaming selection).
2. Build an async generator `chatStream` in the frontend using the ReadableStream API reader on the `fetch` response body to decode Server-Sent Events (SSE) with `data: ` packet blocks.
3. Construct a dual-panel dashboard UI `AIChatAssistant.tsx` featuring search-filterable history log sidebar, configurations control dropdowns, micro-animated message feeds, confidence meters, response timers, follow-up suggestion chips, and citation links.

Reason: Retains secure multi-tenant project isolation boundaries, avoids layout blockage by decoding chunk events in real-time, and exposes grounded evidence links directly inside conversational contexts.

Files affected: `backend/app/models/ai_chat.py`, `backend/app/services/ai.py`, `backend/app/api/routes/ai.py`, `frontend/src/types/ai.ts`, `frontend/src/services/aiApi.ts`, `frontend/src/components/AIChatAssistant.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`

## DEC-018: Knowledge Graph and Interactive Timeline Visualizer

Context: M16 requires a dual interactive interface visualizing the project's knowledge base. It needs an interactive node-link graph rendering connected sources (commits, PRs, Notion pages, files) with full canvas controls (zoom, pan, drag, custom colors) alongside a chronological timeline list with badges and direct relationship traversal.

Decision:
1. Implement `KnowledgeGraphAndTimeline.tsx` containing the canvas rendering pipeline and HTML/CSS layout.
2. Build an HTML5 Canvas node-link visualizer using 2D physics simulation (repulsion, attraction, friction) calculated in a React `requestAnimationFrame` loop.
3. Design interactive mouse event handlers to support node dragging, graph panning (right click / drag), zoom centering, and detail hover states.
4. Scale canvas dimensions dynamically with high-DPI device pixel ratio tracking to keep drawing extremely sharp.
5. Couple visual states: selecting a node in the graph centers the view, updates details sidebar inspectors, highlights linked neighbor edges, and scrolls the timeline feed to highlight the matching card.
6. List all knowledge items in the chronological vertical timeline panel with badge classifications and detail inspector shortcuts.

Reason: By bypassing heavy external visualization libraries (e.g. D3, cytoscape) in favor of a clean, optimized Canvas2D custom simulation loop, we achieve absolute styling flexibility matching our design system tokens, maintain extremely smooth rendering performance, and avoid bundle bloat.

Files affected: `frontend/src/components/KnowledgeGraphAndTimeline.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`

## DEC-019: Engineering Intelligence and Heuristic Insight Strategy Pattern

Context: M17 requires building the "Engineering Intelligence" module which aggregates project health, documentation coverage, architectural decisions, and duplicate knowledge assets, synthesizes these findings using LLMs, and presents them in an interactive developer dashboard.

Decision:
1. Create `EngineeringInsight` SQLAlchemy database model mapping to the `engineering_insights` table to persist structured insight records.
2. Implement a Strategy pattern rule engine with a base `InsightRule` class and 6 concrete heuristic strategy rule classes: DocumentationGapRule, StaleKnowledgeRule, ArchitectureDriftRule, DuplicateKnowledgeRule, ProjectHealthRule, and KnowledgeCoverageRule.
3. Build `InsightService.analyze_project_insights` to run all rules, compile findings into an AI prompt context, invoke the active LLM provider for refinement and severity/confidence weighting, and save/upsert the results.
4. Expose secure REST API routes under project membership and tenant organization checks.
5. Build React dashboard component `EngineeringIntelligence.tsx` displaying KPI metrics, filters (severity, status, type), and a detail inspector for justifications, evidence, and suggested checklist actions.

Reason: The Strategy pattern isolates rules logic for easier expansion. LLM-based refinement turns dry alerts into actionable engineering guides. Project membership checks prevent cross-tenant data leaks.

Files affected: `backend/app/models/insight.py`, `backend/app/services/insight_rules.py`, `backend/app/services/insight.py`, `backend/app/api/routes/insight.py`, `frontend/src/components/EngineeringIntelligence.tsx`, `frontend/src/pages/ProjectDetailPage.tsx`
