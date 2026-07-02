# Deployment Guide

Version: 1.0

Status: Active

---

# Purpose

This document describes how KnowWhy is deployed from local development to a production environment.

The deployment process should be simple, repeatable, and automated.

---

# Deployment Environments

KnowWhy has three environments:

## Development

Purpose

Daily development.

Runs locally using Docker.

---

## Staging

Purpose

Testing before production.

Should mirror the production environment.

---

## Production

Purpose

Live application used by real users.

Must prioritize stability and security.

---

# Technology Stack

Frontend

- React
- Vite

Backend

- FastAPI

Database

- PostgreSQL

Cache

- Redis

Containerization

- Docker

CI/CD

- GitHub Actions

Hosting (MVP)

- Railway

Future

- AWS

---

# Deployment Flow

```
Developer

↓

GitHub

↓

GitHub Actions

↓

Build

↓

Run Tests

↓

Docker Image

↓

Deploy

↓

Production
```

---

# Local Development

Requirements

- Docker Desktop
- Git
- Node.js
- Python
- PostgreSQL (or Docker)

Commands

```bash
git clone <repository>

cd knowWhy

docker compose up
```

The application should start with a single command.

---

# Environment Variables

Frontend

```
VITE_API_URL
```

Backend

```
DATABASE_URL

REDIS_URL

JWT_SECRET

OPENAI_API_KEY

GITHUB_CLIENT_ID

GITHUB_CLIENT_SECRET

GOOGLE_CLIENT_ID

GOOGLE_CLIENT_SECRET
```

Never commit secrets to Git.

---

# Docker

Containers

- Frontend
- Backend
- PostgreSQL
- Redis

Use Docker Compose during development.

---

# CI/CD Pipeline

Every push should:

- Install dependencies
- Run tests
- Build application
- Build Docker image
- Deploy (main branch only)

---

# Database

Before deployment:

- Run migrations
- Verify schema
- Backup database

---

# Deployment Checklist

Before deploying:

- Tests pass
- Environment variables configured
- Database migration completed
- Docker image built
- Production URL verified

---

# Monitoring

Monitor:

- API health
- Database
- Memory usage
- CPU usage
- Error logs

Future Tools

- Grafana
- Prometheus
- Sentry

---

# Rollback

If deployment fails:

1. Stop deployment
2. Restore previous version
3. Restore database if required
4. Investigate issue
5. Redeploy after fix

---

# Deployment Goals

- Zero manual configuration
- Repeatable deployments
- Fast rollback
- Automated testing
- Secure production environment

---

# Summary

KnowWhy should be deployable with minimal manual effort.

The deployment process should remain automated, secure, and reproducible throughout the project's lifecycle.