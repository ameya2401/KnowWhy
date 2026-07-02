# High Level Architecture

Version: 1.0

Status: Draft

---

# Purpose

This document describes the overall architecture of KnowWhy and how the major components interact.

The goal is to provide a high-level understanding of the system before diving into implementation.

---

# System Overview

KnowWhy sits on top of existing developer tools.

It does not replace them.

Instead, it continuously collects information, builds organizational memory, and answers questions using AI.

```
                +----------------------+
                |      Web Client      |
                |  React + TypeScript  |
                +----------+-----------+
                           |
                     HTTPS / REST
                           |
                +----------v-----------+
                |     Backend API      |
                |      FastAPI         |
                +----------+-----------+
                           |
          -----------------------------------------
          |          |          |         |        |
          |          |          |         |        |
          v          v          v         v        v

   PostgreSQL   Vector DB   Redis    File Store   LLM

          |
          |
          v

 Integration Services

 GitHub
 Notion
 Google Drive
 Calendar
 Slack (Future)

```

---

# Major Components

## Frontend

Responsible for:

- Authentication
- Dashboard
- Search
- Memory Explorer
- Timeline
- AI Chat
- Settings

Technology

- React
- TypeScript
- Tailwind CSS
- React Query
- React Router

---

## Backend

Responsible for:

- Business Logic
- Authentication
- APIs
- Memory Construction
- Search
- AI Orchestration

Technology

- FastAPI
- Python

---

## PostgreSQL

Stores:

- Users
- Organizations
- Teams
- Projects
- Documents
- Decisions
- Metadata
- Audit Logs

PostgreSQL is the source of truth.

---

## Vector Database

Stores semantic embeddings for:

- Documents
- PRs
- Issues
- Meetings
- Conversations

Purpose

Semantic Search

Duplicate Detection

Context Retrieval

---

## Redis

Used for:

- Caching
- Session Storage
- Background Jobs
- Rate Limiting

---

## AI Layer

Responsible for:

- Entity Extraction
- Summarization
- Question Answering
- Context Reasoning
- Recommendations

AI never directly accesses raw data.

Everything goes through the Memory Layer.

---

## Integration Layer

Each integration is an independent connector.

Examples

GitHub Connector

Notion Connector

Google Drive Connector

Calendar Connector

Future:

Slack

Discord

Jira

Linear

---

# Request Flow

Example

User asks:

"Why did we migrate to PostgreSQL?"

Flow

User

↓

Frontend

↓

Backend

↓

Memory Engine

↓

Semantic Search

↓

Retrieve Evidence

↓

LLM

↓

Generate Response

↓

Frontend

---

# Data Flow

External Tools

↓

Connector

↓

Raw Events

↓

Processing

↓

Entity Extraction

↓

Memory Builder

↓

Database

↓

Vector Database

↓

AI Retrieval

↓

User

---

# Design Principles

- Modular Architecture
- API First
- AI Independent
- Database Agnostic
- Event Driven
- Explainable AI
- Security First

---

# Initial Tech Stack

Frontend

- React
- TypeScript
- Tailwind CSS

Backend

- FastAPI
- SQLAlchemy
- Pydantic

Database

- PostgreSQL

Vector Search

- pgvector (MVP)
- Qdrant (Future)

Cache

- Redis

Authentication

- OAuth 2.0
- JWT

Deployment

- Docker
- GitHub Actions
- Railway (Development)
- AWS (Future)

AI

- OpenAI / Claude API
- Local Models (Future)

---

# Future Improvements

- Microservices (if required)
- Kubernetes
- Event Streaming
- Multi-Agent AI
- Knowledge Graph
- Plugin System

---

# Key Decisions

- Modular Monolith for MVP
- PostgreSQL as primary database
- pgvector for semantic search
- REST APIs
- Docker-first development
- Cloud agnostic architecture

---

# Summary

KnowWhy consists of six major layers:

1. Frontend
2. Backend
3. Database
4. Memory Layer
5. AI Layer
6. External Integrations

Each layer has a single responsibility and communicates through well-defined interfaces.