# Database Design

Version: 1.0

Status: Draft

---

# Purpose

This document defines the logical database structure of KnowWhy.

KnowWhy uses PostgreSQL as the primary database and pgvector for semantic search.

The database stores structured organizational data, while vector embeddings enable AI-powered retrieval.

---

# Database Strategy

KnowWhy uses a hybrid storage approach.

```
                PostgreSQL
            (Structured Data)
                    │
                    │
             pgvector Extension
          (Semantic Embeddings)
```

PostgreSQL remains the source of truth.

---

# Core Entities

The following entities form the database.

```
Organization
│
├── Users
├── Teams
├── Projects
├── Repositories
├── Documents
├── Meetings
├── Issues
├── Pull Requests
├── Decisions
├── Evidence
└── Audit Logs
```

---

# Entity Relationships

```
Organization
    │
    ├── Users
    │      │
    │      ├── Projects
    │      ├── Meetings
    │      └── Decisions
    │
    ├── Teams
    │
    ├── Repositories
    │      │
    │      ├── Pull Requests
    │      ├── Commits
    │      └── Issues
    │
    └── Documents
```

---

# Main Tables

## organizations

Stores company information.

Fields

- id
- name
- created_at

---

## users

Stores authenticated users.

Fields

- id
- organization_id
- name
- email
- role
- avatar_url

---

## teams

Stores teams inside an organization.

Fields

- id
- organization_id
- name

---

## projects

Stores software projects.

Fields

- id
- organization_id
- team_id
- name
- description

---

## repositories

Connected Git repositories.

Fields

- id
- project_id
- provider
- repository_name
- repository_url

---

## documents

Knowledge sources.

Examples

- Notion
- Google Docs
- Markdown
- PDFs

Fields

- id
- project_id
- title
- source
- content
- embedding

---

## meetings

Meeting metadata.

Fields

- id
- project_id
- title
- meeting_date
- transcript

---

## issues

Imported issues.

Fields

- id
- repository_id
- title
- description
- status

---

## pull_requests

GitHub Pull Requests.

Fields

- id
- repository_id
- author_id
- title
- status

---

## decisions

The most important table.

Stores organizational decisions.

Fields

- id
- project_id
- title
- summary
- confidence
- created_by
- created_at

---

## evidence

Stores supporting evidence.

Fields

- id
- decision_id
- source
- source_type
- reference

---

## audit_logs

Security and tracking.

Fields

- id
- user_id
- action
- timestamp

---

# Embeddings

The following content will have embeddings.

- Documents
- Meeting transcripts
- Pull Requests
- Issues
- Comments
- Decision summaries

These embeddings are stored using pgvector.

---

# Indexes

Important indexes.

- email
- organization_id
- project_id
- repository_id
- created_at
- vector index (HNSW)

Indexes improve search performance.

---

# Relationships

Primary Keys

UUID

Foreign Keys

Organization → Users

Organization → Teams

Teams → Projects

Projects → Repositories

Repositories → Pull Requests

Projects → Documents

Projects → Meetings

Projects → Decisions

Decisions → Evidence

---

# Soft Deletes

KnowWhy should avoid permanently deleting data.

Every major table should include

- created_at
- updated_at
- deleted_at

Deleted records remain recoverable.

---

# Search Strategy

Normal Search

PostgreSQL Full Text Search

Semantic Search

pgvector

Future

Hybrid Search

Keyword + Semantic

---

# Backup Strategy

Daily database backups.

Point-in-time recovery.

Encrypted backups.

---

# Security

Sensitive information should never be stored in plaintext.

Encrypt

- OAuth Tokens
- API Keys
- Secrets

Passwords will never be stored directly.

OAuth authentication will be used.

---

# Future Tables

Future versions may introduce:

- workflows
- recommendations
- agents
- memory_graph
- notifications
- automations

These are intentionally excluded from Version 1.

---

# Database Principles

- PostgreSQL is the source of truth.
- Every entity belongs to an organization.
- Use UUIDs for all primary keys.
- Prefer normalization over duplication.
- Never store AI-generated facts without evidence.
- Store metadata separately from embeddings.

---

# Summary

KnowWhy stores structured organizational knowledge in PostgreSQL and semantic representations using pgvector.

This hybrid design provides:

- Reliable transactions
- Fast filtering
- Semantic search
- AI context retrieval
- Easy scalability

The database is designed to support the MVP while remaining extensible for future AI and knowledge graph features.