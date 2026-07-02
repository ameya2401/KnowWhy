# Development Workflow

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines how KnowWhy will be developed.

The goal is to maintain clean code, consistent commits, and an organized development process.

---

# Development Cycle

Every feature follows this workflow.

```
Backlog

↓

Design

↓

Development

↓

Testing

↓

Review

↓

Merge

↓

Deploy
```

---

# Git Branches

Main Branch

```
main
```

Development Branch

```
develop
```

Feature Branches

```
feature/auth

feature/github-sync

feature/search

feature/ai-chat
```

Bug Fixes

```
fix/login

fix/search

fix/api
```

---

# Commit Convention

Use meaningful commit messages.

Examples

```
feat: add GitHub OAuth

feat: implement semantic search

fix: resolve login bug

refactor: simplify memory service

docs: update API documentation

test: add authentication tests

style: format frontend components
```

---

# Pull Request Checklist

Before merging:

- Code compiles
- Tests pass
- No secrets committed
- No unnecessary files
- Documentation updated (if required)
- Feature tested manually

---

# Coding Workflow

1. Pick a task from the backlog.
2. Create a feature branch.
3. Implement the feature.
4. Test locally.
5. Commit changes.
6. Create a Pull Request.
7. Review.
8. Merge into `develop`.
9. Merge `develop` into `main` after a stable milestone.

---

# Testing

Backend

- Unit Tests
- API Tests

Frontend

- Component Tests
- Integration Tests

Before every release:

- Manual testing
- End-to-end smoke test

---

# Code Reviews

Every Pull Request should check:

- Readability
- Naming
- Performance
- Security
- Reusability
- Simplicity

---

# Environment

Use separate environments.

Development

```
.env.development
```

Testing

```
.env.test
```

Production

```
.env.production
```

Never commit `.env` files.

---

# Release Strategy

MVP

```
v0.1.0
```

Feature Releases

```
v0.2.0

v0.3.0
```

Stable Release

```
v1.0.0
```

Follow Semantic Versioning:

- MAJOR.MINOR.PATCH

---

# Documentation Rule

Update documentation only when:

- Architecture changes
- API changes
- Database changes
- New feature is added

Avoid documenting every minor implementation detail.

---

# Development Principles

- Build one feature at a time.
- Keep Pull Requests small.
- Test before merging.
- Write readable code.
- Refactor when necessary.
- Finish features before starting new ones.

---

# Summary

The workflow prioritizes consistency, collaboration, and maintainability.

Following the same process for every feature reduces bugs and makes the project easier to manage as it grows.