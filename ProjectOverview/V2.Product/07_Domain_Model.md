# Domain Model

Version: 1.0

Status: Draft

Authors:
- Ameya Bhagat
- Project Partner

---

# Purpose

This document defines the core entities that exist inside KnowWhy.

Rather than designing the database first, KnowWhy follows a domain-first approach.

Every API, AI model, database schema, user interface, and workflow will ultimately revolve around these domain entities.

The purpose of this document is to answer one question:

> "What does KnowWhy actually understand?"

KnowWhy does not understand tables.

KnowWhy understands organizations.

---

# Why Domain Modeling?

Traditional student projects usually begin by creating database tables.

KnowWhy intentionally avoids this approach.

Instead,

KnowWhy first defines real-world concepts.

Only afterwards will these concepts become:

- Database Tables
- API Objects
- Graph Nodes
- Vector Documents
- Search Indexes
- Machine Learning Features

This separation keeps the architecture clean.

---

# Core Philosophy

Everything inside KnowWhy should represent something that exists inside an organization.

If something cannot be described as a meaningful organizational concept,

it probably should not exist as a first-class entity.

---

# Entity Categories

The KnowWhy domain consists of six major groups.

1. Organization

2. People

3. Work

4. Knowledge

5. Communication

6. Intelligence

---

# Organization

Represents the company using KnowWhy.

Properties

- Organization ID
- Name
- Industry
- Timezone
- Subscription
- Integrations
- Teams

Relationships

Organization

↓

Teams

↓

Projects

↓

People

---

# Team

Represents a functional group.

Examples

Backend Team

Frontend Team

DevOps Team

Product Team

Design Team

Relationships

Team

↓

Members

↓

Projects

↓

Meetings

↓

Repositories

---

# Person

Represents an individual.

Examples

Developer

Manager

Founder

Designer

Intern

Properties

- Name
- Email
- Role
- Skills
- Teams
- Permissions

Relationships

Person

↓

Meetings

↓

Tasks

↓

Documents

↓

Commits

↓

Messages

↓

Decisions

---

# Project

Represents work toward one business objective.

Examples

KnowWhy

Mobile App

Internal Dashboard

Website

Relationships

Project

↓

Repositories

↓

Meetings

↓

Documents

↓

Tasks

↓

Discussions

↓

Decisions

---

# Repository

Represents a source code repository.

Properties

- URL
- Branches
- Pull Requests
- Issues
- Commits

Relationships

Repository

↓

Project

↓

Commits

↓

Developers

↓

Releases

---

# Issue

Represents work needing attention.

Examples

Bug

Feature

Task

Enhancement

Relationships

Issue

↓

Repository

↓

Pull Request

↓

Discussion

↓

Decision

---

# Pull Request

Represents proposed code changes.

Relationships

PR

↓

Commits

↓

Reviewers

↓

Comments

↓

Decision

---

# Commit

Represents one code contribution.

Relationships

Commit

↓

Developer

↓

Issue

↓

Repository

↓

Release

---

# Document

Represents structured knowledge.

Examples

Notion

Google Docs

Markdown

Architecture Notes

RFC

Relationships

Document

↓

Project

↓

People

↓

Meetings

↓

Decisions

↓

Evidence

---

# Meeting

Represents discussions.

Examples

Sprint Planning

Architecture Review

Standup

Retrospective

Relationships

Meeting

↓

Participants

↓

Agenda

↓

Recording

↓

Transcript

↓

Decisions

↓

Action Items

---

# Conversation

Represents communication.

Examples

Slack

Discord

Email

Teams

Relationships

Conversation

↓

Messages

↓

People

↓

Projects

↓

Issues

↓

Decisions

---

# Decision

One of KnowWhy' most important entities.

Represents a finalized organizational decision.

Examples

Choose PostgreSQL

Reject MongoDB

Use OAuth

Adopt FastAPI

Properties

Decision

Reason

Evidence

Date

Participants

Confidence

Alternatives

Relationships

Decision

↓

Evidence

↓

Meetings

↓

Discussions

↓

Documents

↓

Project

---

# Evidence

Every AI answer should reference evidence.

Evidence can come from

Documents

Messages

Meetings

Emails

Pull Requests

Commits

Issues

Evidence exists so KnowWhy never becomes a black box.

---

# Event

Represents something that happened.

Examples

PR Merged

Issue Closed

Meeting Scheduled

Document Updated

Deployment Completed

Events become the timeline of organizational memory.

---

# Task

Represents work assigned.

Relationships

Task

↓

Project

↓

Person

↓

Decision

↓

Deadline

↓

Status

---

# Relationship

KnowWhy stores relationships as first-class citizens.

Examples

Developer

↓

Worked On

↓

Repository

Meeting

↓

Produced

↓

Decision

Issue

↓

Resolved By

↓

Pull Request

Document

↓

References

↓

Architecture

Relationship strength may change over time.

---

# Memory

Memory is NOT a database table.

Memory is an intelligent representation of relationships between entities.

Memory combines

People

Projects

Events

Evidence

Decisions

Documents

Conversations

Tasks

Repositories

into one connected understanding.

---

# Organizational Timeline

Everything KnowWhy learns eventually becomes a timeline.

Example

Meeting

↓

Decision

↓

Issue Created

↓

PR

↓

Review

↓

Merge

↓

Deployment

↓

Customer Feedback

↓

Next Decision

Instead of isolated records,

KnowWhy stores history.

---

# Domain Graph

Conceptually,

KnowWhy understands organizations like a graph.

Organization

↓

Team

↓

Project

↓

Repository

↓

Issue

↓

Pull Request

↓

Commit

↓

Decision

↓

Evidence

↓

Timeline

↓

Memory

This graph becomes the backbone of AI reasoning.

---

# Entity Priorities

Version 1

Organization

Team

Person

Project

Repository

Issue

Pull Request

Document

Meeting

Decision

Evidence

Version 2

Task

Conversation

Event

Recommendation

Workflow

Automation

Version 3

Knowledge Graph

Agent

Prediction

Optimization

Learning Model

---

# Design Rules

Every new entity must answer:

Does this exist in the real world?

Does it solve a user problem?

Does AI need to understand it?

Does another entity already represent it?

Can it be connected to evidence?

If the answer is "No",

the entity should not exist.

---

# Closing Statement

KnowWhy is not built around software objects.

KnowWhy is built around organizational concepts.

Everything else—

the database,

the APIs,

the AI,

the user interface,

the search engine,

and the workflow engine—

should naturally emerge from this domain model.

If the domain model is correct,

the software architecture will become significantly easier to design and maintain.