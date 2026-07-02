# User Flows

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines the primary user journeys in KnowWhy.

The goal is to ensure every important workflow is simple, intuitive, and requires the fewest possible steps.

---

# User Flow 1 — First Time Setup

```
Landing Page

↓

Login

↓

Create Organization

↓

Connect GitHub

↓

Connect Notion

↓

Connect Google Drive

↓

Initial Synchronization

↓

Dashboard
```

Goal

User should reach a working dashboard in less than 10 minutes.

---

# User Flow 2 — Ask AI

```
Dashboard

↓

Search / AI Chat

↓

Enter Question

↓

Retrieve Context

↓

Generate Response

↓

Display Answer

↓

View Sources

↓

Open Original Document
```

Example

User asks:

"Why do we use PostgreSQL?"

KnowWhy returns:

- Answer
- Confidence
- Timeline
- Supporting Documents

---

# User Flow 3 — Search

```
Search

↓

Type Query

↓

Suggestions

↓

Results

↓

Filters

↓

Open Result

↓

Related Content
```

Search should support:

- Natural language
- Keywords
- Recent searches

---

# User Flow 4 — Browse Projects

```
Dashboard

↓

Projects

↓

Select Project

↓

Project Overview

↓

Repositories

↓

Documents

↓

Meetings

↓

Decisions
```

---

# User Flow 5 — Timeline

```
Dashboard

↓

Timeline

↓

Select Event

↓

View Details

↓

Related Events

↓

Supporting Evidence
```

---

# User Flow 6 — Integration

```
Settings

↓

Integrations

↓

Choose Platform

↓

OAuth Login

↓

Grant Permission

↓

Start Sync

↓

Success
```

---

# User Flow 7 — Organization Management

```
Settings

↓

Organization

↓

Invite Member

↓

Assign Role

↓

Save
```

---

# User Flow 8 — User Profile

```
Avatar

↓

Profile

↓

Account Settings

↓

Connected Accounts

↓

Logout
```

---

# Navigation Map

```
Dashboard

├── Projects
├── Search
├── AI Chat
├── Timeline
├── Integrations
└── Settings
```

Every page should be reachable within two or three clicks.

---

# Error Flow

Example

GitHub connection fails

```
Connect GitHub

↓

Error

↓

Display Message

↓

Retry
```

Never leave users without guidance.

---

# Empty Flow

Example

No projects

```
Projects

↓

Empty State

↓

Create Project
```

Every empty page should include a clear call-to-action.

---

# Success Flow

Example

Question Answered

```
Ask Question

↓

Answer Generated

↓

Evidence Displayed

↓

Open Source

↓

Continue Exploring
```

Encourage users to explore related information.

---

# Design Goals

Every user flow should:

- Require minimal clicks
- Provide clear feedback
- Handle errors gracefully
- Be easy for first-time users

---

# Summary

KnowWhy is designed around simple, efficient workflows.

Users should spend their time understanding their organization's knowledge—not figuring out how to use the application.