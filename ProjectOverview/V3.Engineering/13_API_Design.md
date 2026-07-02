# API Design

Version: 1.0

Status: Draft

---

# Purpose

This document defines the major REST APIs required for KnowWhy MVP.

The goal is to provide a clear contract between the frontend and backend.

---

# API Principles

- RESTful APIs
- JSON Request/Response
- JWT Authentication
- Versioned APIs (`/api/v1`)
- Consistent Error Responses

Base URL

```
/api/v1
```

---

# Authentication

## Login

```
POST /auth/login
```

Returns JWT token.

---

## Logout

```
POST /auth/logout
```

---

## Current User

```
GET /auth/me
```

Returns logged-in user details.

---

# Organizations

## Get Organization

```
GET /organizations/:id
```

---

## Create Organization

```
POST /organizations
```

---

## Update Organization

```
PUT /organizations/:id
```

---

# Users

## Get Users

```
GET /users
```

---

## Invite User

```
POST /users/invite
```

---

## Update User Role

```
PATCH /users/:id
```

---

# Projects

## Get Projects

```
GET /projects
```

---

## Create Project

```
POST /projects
```

---

## Project Details

```
GET /projects/:id
```

---

# Integrations

## List Integrations

```
GET /integrations
```

---

## Connect GitHub

```
POST /integrations/github
```

---

## Connect Notion

```
POST /integrations/notion
```

---

## Connect Google Drive

```
POST /integrations/google-drive
```

---

## Sync Integration

```
POST /integrations/:id/sync
```

---

# Search

## Semantic Search

```
POST /search
```

Request

```json
{
  "query": "Why did we migrate to PostgreSQL?"
}
```

Response

```json
{
  "results": [],
  "sources": [],
  "confidence": 0.92
}
```

---

# AI

## Ask KnowWhy

```
POST /ai/chat
```

Request

```json
{
  "question": "Why do we use Redis?"
}
```

Response

```json
{
  "answer": "...",
  "sources": [],
  "timeline": [],
  "confidence": 0.91
}
```

---

# Documents

## List Documents

```
GET /documents
```

---

## Document Details

```
GET /documents/:id
```

---

# Meetings

## Get Meetings

```
GET /meetings
```

---

## Meeting Details

```
GET /meetings/:id
```

---

# Decisions

## List Decisions

```
GET /decisions
```

---

## Decision Timeline

```
GET /decisions/:id/timeline
```

---

# Health

```
GET /health
```

Used for deployment monitoring.

---

# Error Format

Example

```json
{
    "success": false,
    "message": "Project not found",
    "error_code": "PROJECT_NOT_FOUND"
}
```

---

# Success Format

Example

```json
{
    "success": true,
    "data": {}
}
```

---

# Authentication Flow

```
User

↓

OAuth Login

↓

JWT Token

↓

Frontend Stores Token

↓

API Requests

↓

Backend Verification
```

---

# Future APIs

Not part of MVP

- Workflow Automation
- Recommendations
- Notifications
- Agents
- Analytics
- Plugin APIs

---

# Summary

The API layer exposes all KnowWhy functionality through a clean REST interface.

The API should remain simple, consistent, and independent of frontend implementation.