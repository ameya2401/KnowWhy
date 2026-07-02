# Project Structure

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines the folder structure, coding conventions, and architecture of KnowWhy.

The goal is to keep the project organized, scalable, and easy to maintain.

---

# Repository Structure

```
knowWhy/

├── frontend/
├── backend/
├── ai/
├── database/
├── workers/
├── docs/
├── docker/
├── scripts/
├── tests/
├── .github/
├── .env.example
├── docker-compose.yml
└── README.md
```

---

# Frontend Structure

```
frontend/

src/

├── components/
├── pages/
├── layouts/
├── hooks/
├── services/
├── store/
├── types/
├── utils/
├── assets/
├── routes/
└── App.tsx
```

### Responsibilities

**components/**

Reusable UI components.

**pages/**

Application screens.

**layouts/**

Dashboard layout, Auth layout.

**hooks/**

Custom React hooks.

**services/**

API calls.

**store/**

Global state.

**types/**

TypeScript interfaces.

**utils/**

Helper functions.

---

# Backend Structure

```
backend/

app/

├── api/
├── core/
├── models/
├── schemas/
├── services/
├── repositories/
├── integrations/
├── ai/
├── workers/
├── utils/
└── main.py
```

### Responsibilities

**api/**

REST endpoints.

**models/**

SQLAlchemy models.

**schemas/**

Pydantic schemas.

**services/**

Business logic.

**repositories/**

Database operations.

**integrations/**

GitHub, Notion, Google APIs.

**ai/**

LLM, embeddings, RAG.

**workers/**

Background jobs.

---

# Layered Architecture

```
Frontend

↓

API

↓

Services

↓

Repositories

↓

Database
```

Rules

- API never talks directly to Database.
- Business logic belongs in Services.
- Database logic belongs in Repositories.

---

# Configuration

Environment variables

```
DATABASE_URL

OPENAI_API_KEY

GITHUB_CLIENT_ID

GITHUB_CLIENT_SECRET

GOOGLE_CLIENT_ID

GOOGLE_CLIENT_SECRET

JWT_SECRET

REDIS_URL
```

Never commit secrets.

---

# State Management

Frontend

- React Query
- Context API

Backend

- Stateless APIs
- Redis for cache

---

# Naming Conventions

Files

```
user_service.py

github_connector.py

memory_engine.py
```

Classes

```
UserService

MemoryBuilder

GitHubConnector
```

React Components

```
ProjectCard.tsx

Sidebar.tsx

SearchBar.tsx
```

---

# Coding Standards

- Follow PEP 8 (Python)
- Follow ESLint + Prettier (React)
- Use meaningful variable names
- Write small reusable functions
- Avoid duplicate code

---

# Error Handling

Every API should return

```
{
  success,
  data,
  message
}
```

Avoid exposing internal errors.

Log detailed errors internally.

---

# Logging

Log

- API requests
- AI calls
- Background jobs
- Integration syncs
- Errors

---

# Testing

Frontend

- Vitest
- React Testing Library

Backend

- Pytest

Goal

At least 70% test coverage.

---

# Documentation

Every module should contain:

- Purpose
- Inputs
- Outputs
- Dependencies

Public functions should include docstrings.

---

# Git Strategy

Main Branch

```
main
```

Development

```
develop
```

Feature Branch

```
feature/github-integration

feature/memory-engine

feature/semantic-search
```

Bug Fix

```
fix/login-bug
```

---

# Principles

- Keep modules independent.
- Keep functions small.
- Prefer readability over cleverness.
- Build reusable components.
- Write code for future contributors.
- Refactor when necessary.

---

# Summary

KnowWhy follows a clean, layered architecture with clear separation of concerns.

Every folder has a single responsibility, making the project easier to scale, maintain, and understand.