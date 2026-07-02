# Tech Stack

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines the technology stack for KnowWhy MVP.

The primary goals while selecting technologies were:

- Industry relevance
- Learning value
- Community support
- Scalability
- Ease of development

Technology should solve problems, not create them.

---

# Overview

| Layer | Technology |
|---------|------------|
| Frontend | React + TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Backend | FastAPI (Python) |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Cache | Redis |
| Authentication | OAuth 2.0 + JWT |
| AI | OpenAI / Claude APIs |
| File Storage | Google Drive (initial) |
| Background Jobs | Celery + Redis |
| Containerization | Docker |
| Version Control | Git + GitHub |
| CI/CD | GitHub Actions |
| Deployment | Railway (Dev), AWS (Future) |

---

# Frontend

## React

Reason

- Industry standard
- Huge ecosystem
- Component-based architecture
- Excellent TypeScript support

---

## TypeScript

Reason

- Type safety
- Better maintainability
- Fewer runtime bugs
- Standard in modern frontend development

---

## Tailwind CSS

Reason

- Fast development
- Consistent design
- Easy customization
- Large community

---

## shadcn/ui

Reason

- Modern UI
- Accessible components
- Easily customizable
- No vendor lock-in

---

# Backend

## FastAPI

Reason

- High performance
- Automatic OpenAPI documentation
- Async support
- Easy AI integration
- Excellent Python ecosystem

---

## SQLAlchemy

Reason

- Mature ORM
- Flexible
- Supports PostgreSQL
- Easy migrations

---

## Pydantic

Reason

- Validation
- Serialization
- Type safety
- Native FastAPI integration

---

# Database

## PostgreSQL

Reason

- Reliable
- ACID compliant
- Excellent indexing
- JSON support
- pgvector support

---

## pgvector

Reason

- Native PostgreSQL extension
- Simple setup
- No separate vector database
- Ideal for MVP

Future

Qdrant can be introduced if scaling requires it.

---

# AI

## OpenAI / Claude APIs

Reason

- Best reasoning quality
- Rapid development
- No model training required

Future

Support for local models:

- Llama
- Qwen
- Mistral

---

# Authentication

OAuth Providers

- GitHub
- Google

Reason

No password management.

Better security.

Better user experience.

---

# Caching

Redis

Used for:

- Session caching
- API caching
- Rate limiting
- Background jobs

---

# Background Processing

Celery + Redis

Used for

- GitHub synchronization
- Document indexing
- Embedding generation
- Scheduled jobs

---

# Development Tools

IDE

- VS Code

API Testing

- Postman
- Bruno

Database

- pgAdmin

Container

- Docker Desktop

---

# DevOps

Docker

Reason

Consistent development environment.

GitHub Actions

Reason

Automatic testing.

Automatic deployment.

---

# Monitoring (Future)

- Grafana
- Prometheus
- Sentry

Not required for MVP.

---

# Project Structure

```

knowWhy/

├── frontend/

├── backend/

├── docs/

├── docker/

├── scripts/

├── database/

├── ai/

├── workers/

├── tests/

└── .github/

```

---

# Future Technologies

Possible future additions

- Neo4j
- Qdrant
- Kubernetes
- Temporal
- Apache Kafka
- LangGraph

These are intentionally postponed until the MVP demonstrates real need.

---

# Technologies We Considered

| Technology | Decision | Reason |
|------------|----------|--------|
| Spring Boot | ❌ | FastAPI better aligns with AI ecosystem |
| MongoDB | ❌ | PostgreSQL offers stronger relational modeling |
| Next.js | ❌ | React SPA is sufficient for MVP |
| Firebase | ❌ | Vendor lock-in and limited backend flexibility |
| Qdrant | Later | pgvector is simpler for MVP |
| Kubernetes | Later | Overkill for MVP |
| Microservices | Later | Modular Monolith is simpler |

---

# Final Stack

Frontend

- React
- TypeScript
- Tailwind
- shadcn/ui

Backend

- FastAPI
- SQLAlchemy
- Pydantic

Database

- PostgreSQL
- pgvector

Infrastructure

- Docker
- Redis
- GitHub Actions

AI

- OpenAI / Claude

Deployment

- Railway (Development)
- AWS (Production)

---

# Summary

The selected technology stack prioritizes learning, maintainability, and rapid development while remaining scalable enough to evolve into a production-ready platform.

No technology has been selected simply because it is popular. Every choice supports the long-term vision of KnowWhy while keeping the MVP achievable for a two-person development team.