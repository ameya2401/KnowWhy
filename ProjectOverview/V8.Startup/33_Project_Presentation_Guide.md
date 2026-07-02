# Project Presentation Guide

Version: 1.0

Status: Active

---

# Purpose

This document provides different ways to explain KnowWhy depending on the audience and available time.

It also contains common questions and recommended answers.

---

# One-Line Pitch

KnowWhy is an AI-powered Organizational Intelligence Platform that helps software teams preserve, search, and understand their collective knowledge across multiple tools.

---

# 30-Second Elevator Pitch

Modern software teams use GitHub, Notion, Google Drive, Slack, and many other tools. As projects grow, knowledge becomes fragmented, making onboarding and decision-making difficult.

KnowWhy connects these tools, builds a centralized organizational memory, and allows users to ask natural language questions like:

"Why did we migrate to PostgreSQL?"

Instead of manually searching through multiple platforms, KnowWhy retrieves relevant information, provides evidence-backed answers, and helps teams understand their own history.

---

# 2-Minute Project Explanation

KnowWhy solves the problem of knowledge fragmentation inside software teams.

Instead of replacing existing tools, it connects to platforms like GitHub, Notion, Google Drive, and Calendar, continuously collecting organizational knowledge.

This information is processed and stored inside a centralized memory system.

When users ask questions, KnowWhy performs semantic search, retrieves relevant organizational context, and generates AI-powered answers supported by real evidence.

Our goal is to reduce onboarding time, improve knowledge sharing, and make historical project decisions easily discoverable.

---

# 10-Minute Presentation Flow

## 1. Introduction (1 min)

- Introduce the problem.
- Explain why existing workflows are inefficient.

---

## 2. Problem Statement (1 min)

Discuss:

- Knowledge fragmentation
- Information overload
- Difficult onboarding
- Lost organizational context

---

## 3. Existing Solutions (1 min)

Explain why current tools are insufficient:

- Work in isolation
- Limited contextual understanding
- Manual searching

---

## 4. Proposed Solution (2 min)

Explain KnowWhy.

Show:

GitHub

↓

Notion

↓

Google Drive

↓

KnowWhy Memory Engine

↓

AI

↓

User

---

## 5. Architecture (2 min)

Explain:

Frontend

↓

Backend

↓

Database

↓

Memory Layer

↓

AI Layer

↓

External Integrations

---

## 6. Demo (2 min)

Suggested demo:

- Login
- Connect GitHub
- View Dashboard
- Ask AI a question
- Show evidence
- Open original source

---

## 7. Future Scope (1 min)

Explain future possibilities:

- Slack
- Jira
- Knowledge Graph
- Workflow Intelligence
- AI Recommendations

---

# Explaining the AI

KnowWhy does not train its own Large Language Model.

Instead it:

1. Collects organizational knowledge.
2. Creates embeddings.
3. Retrieves relevant information.
4. Sends context to an LLM.
5. Generates an evidence-backed response.

This approach is known as Retrieval-Augmented Generation (RAG).

---

# Technical Highlights

- React
- TypeScript
- FastAPI
- PostgreSQL
- pgvector
- Docker
- OAuth
- RAG
- REST APIs

---

# Why We Built KnowWhy

Our goals were:

- Solve a real problem.
- Learn modern software engineering.
- Build a startup-quality product.
- Prepare for placements.
- Create a research-worthy project.

---

# Common Questions

## Why not use ChatGPT?

ChatGPT has general knowledge but does not understand an organization's private data.

KnowWhy retrieves information from the organization's own tools before generating answers.

---

## Why PostgreSQL?

It provides reliable relational storage and supports vector search through pgvector, allowing both structured queries and semantic search.

---

## Why FastAPI?

FastAPI offers excellent performance, automatic API documentation, and integrates naturally with Python's AI ecosystem.

---

## How is KnowWhy different from enterprise search tools?

KnowWhy focuses on organizational memory rather than simple document search.

It aims to explain *why* decisions were made, not just locate documents.

---

## Why is this useful?

Software teams spend significant time searching for historical information.

KnowWhy reduces this effort by making organizational knowledge searchable through natural language.

---

## Can this become a business?

Yes.

The MVP targets startups and small engineering teams.

Future versions can expand to larger organizations with additional integrations and enterprise features.

---

# Demo Checklist

Before every presentation:

- Application starts successfully.
- Login works.
- Integrations are connected.
- Sample data available.
- AI responses working.
- Internet connection verified.
- Backup screenshots prepared.

---

# Presentation Tips

- Start with the problem, not the technology.
- Explain the value before the implementation.
- Keep diagrams simple.
- Demonstrate working features.
- Be honest about current limitations.
- End with future vision.

---

# Summary

KnowWhy is more than a college project.

It demonstrates end-to-end software engineering, AI integration, modern system design, and product thinking while solving a practical problem faced by software teams.