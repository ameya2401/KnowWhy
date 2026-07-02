# MVP Definition

Version: 1.0

Status: Active

Authors:
- Ameya Bhagat
- Project Partner

---

# Purpose

This document defines the exact scope of Version 1 (MVP) of KnowWhy.

One of the biggest reasons software projects fail is because the first version attempts to solve too many problems simultaneously.

KnowWhy intentionally rejects that approach.

The MVP exists to validate the core hypothesis of KnowWhy with the smallest possible product that still provides meaningful value.

This document answers one question:

> What is the smallest version of KnowWhy that proves our core idea?

---

# Core Hypothesis

KnowWhy is based on the following hypothesis:

Software teams lose valuable organizational context because information is fragmented across multiple tools.

If KnowWhy continuously builds organizational memory and allows teams to retrieve contextual knowledge through natural language, users will save time and make better decisions.

The MVP exists only to validate this hypothesis.

Nothing else.

---

# MVP Philosophy

The MVP is not a simplified version of the final product.

The MVP is an experiment.

Its purpose is learning.

The MVP should answer:

- Does the problem exist?
- Do users care?
- Will users use KnowWhy?
- Which capabilities are genuinely valuable?
- Which assumptions were incorrect?

---

# Primary User

Version 1 targets:

Software teams with 5–25 members.

These teams typically use:

- GitHub
- Notion
- Google Drive
- Google Calendar

Slack support may be added if time permits.

---

# User Story

A developer joins an existing project.

Instead of spending hours searching through:

- GitHub
- Slack
- Notion
- Google Drive
- Meeting notes

they ask KnowWhy:

"Why do we use PostgreSQL?"

KnowWhy reconstructs:

- previous discussions
- architecture documents
- pull requests
- commits
- meeting notes

and provides one evidence-backed explanation.

If KnowWhy can successfully perform this task,

the MVP has achieved its primary objective.

---

# MVP Goals

KnowWhy Version 1 must demonstrate five capabilities.

---

## Goal 1

Collect organizational information.

Supported integrations:

GitHub

Notion

Google Drive

Google Calendar

---

## Goal 2

Construct organizational memory.

KnowWhy should identify:

Projects

People

Repositories

Documents

Meetings

Decisions

Relationships

---

## Goal 3

Provide semantic search.

Users should search naturally.

Examples:

Why OAuth?

Who worked on authentication?

Where was caching discussed?

---

## Goal 4

Explain answers.

Every answer should include:

Evidence

Confidence

Timeline

Source references

---

## Goal 5

Learn continuously.

New commits,

documents,

meetings,

and discussions

should automatically improve memory.

---

# Features Included

Authentication

Organization creation

Team management

GitHub connector

Notion connector

Google Drive connector

Google Calendar connector

Data synchronization

Memory construction

Semantic search

Evidence viewer

Decision timeline

AI question answering

Basic administration

Audit logs

---

# Features Excluded

Workflow automation

AI agents

Notifications

Email integration

Slack integration (optional)

Recommendation engine

Knowledge graph visualization

Expert recommendation

Workflow prediction

Task management

Chat interface

Mobile application

Browser extension

Marketplace

Plugins

Self-hosting

Enterprise permissions

Billing

Analytics dashboard

These features are intentionally postponed.

---

# User Journey

Step 1

Create organization.

↓

Step 2

Connect GitHub.

↓

Step 3

Connect Notion.

↓

Step 4

Connect Drive.

↓

Step 5

KnowWhy synchronizes.

↓

Step 6

Memory builds.

↓

Step 7

User asks question.

↓

Step 8

KnowWhy retrieves evidence.

↓

Step 9

KnowWhy answers with context.

---

# Success Metrics

The MVP succeeds if users can answer questions faster than manual searching.

Metrics include:

Average search time.

Average response latency.

Context accuracy.

Evidence coverage.

User satisfaction.

Daily active users.

Questions answered.

Memory completeness.

---

# Failure Criteria

The MVP fails if:

Users still prefer manual searching.

AI answers cannot be trusted.

Evidence is missing.

Synchronization fails frequently.

Context reconstruction is inaccurate.

Memory quality remains poor.

---

# Technical Constraints

The MVP should:

Remain deployable by two developers.

Use free or low-cost infrastructure where possible.

Avoid unnecessary distributed systems.

Avoid premature optimization.

Favor simplicity over scalability.

---

# Timeline

Research

↓

Architecture

↓

UI/UX

↓

Backend

↓

Integrations

↓

Memory Engine

↓

AI

↓

Testing

↓

Deployment

↓

User Testing

---

# Exit Criteria

Version 1 is complete when:

A software engineering team can install KnowWhy,

connect their tools,

wait for synchronization,

ask organizational questions,

receive evidence-backed answers,

and reconstruct historical decisions without manually searching multiple applications.

Nothing more is required for the MVP.

---

# Closing Statement

The purpose of Version 1 is not to impress users with AI.

Its purpose is to prove that organizational memory can meaningfully reduce the effort required to understand historical organizational context.

Every feature that does not contribute toward validating this hypothesis belongs in a future release.