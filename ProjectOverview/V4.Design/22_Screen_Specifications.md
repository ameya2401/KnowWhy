# Screen Specifications

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines every screen in the KnowWhy MVP.

For each screen, it specifies:

- Purpose
- Main Components
- APIs Used
- Navigation
- Priority

This document acts as the bridge between Figma and frontend development.

---

# Screen 1 — Login

## Purpose

Authenticate users using Google or GitHub OAuth.

## Components

- KnowWhy Logo
- Welcome Text
- Continue with Google
- Continue with GitHub

## APIs

POST /auth/login

## Navigation

Success →

Dashboard

Priority

🔴 High

---

# Screen 2 — Dashboard

## Purpose

Provide a quick overview of the organization.

## Components

- Navbar
- Sidebar
- Recent Activity
- AI Insights
- Recent Decisions
- Connected Integrations

## APIs

GET /projects

GET /users

GET /dashboard

## Navigation

Projects

Search

AI Chat

Timeline

Settings

Priority

🔴 High

---

# Screen 3 — Projects

## Purpose

Display all projects.

## Components

- Project List
- Search
- Filter
- Create Project Button

## APIs

GET /projects

POST /projects

Navigation

Project Details

Priority

🔴 High

---

# Screen 4 — Project Details

## Purpose

View project information.

## Components

- Project Overview
- Repositories
- Documents
- Meetings
- Decisions

## APIs

GET /projects/:id

Priority

🟡 Medium

---

# Screen 5 — Search

## Purpose

Search organizational knowledge.

## Components

- Search Bar
- Filters
- Search Results
- Recent Searches

## APIs

POST /search

Priority

🔴 High

---

# Screen 6 — AI Chat

## Purpose

Allow users to ask KnowWhy questions.

## Components

- Chat Window
- Prompt Box
- Sources Panel
- Confidence Badge
- Timeline

## APIs

POST /ai/chat

Priority

🔴 High

---

# Screen 7 — Timeline

## Purpose

Visualize organizational history.

## Components

- Timeline
- Event Cards
- Filters

## APIs

GET /timeline

Priority

🟡 Medium

---

# Screen 8 — Integrations

## Purpose

Manage external integrations.

## Components

- Integration Cards
- Connect Button
- Sync Status

## APIs

GET /integrations

POST /integrations/github

POST /integrations/notion

POST /integrations/google-drive

Priority

🟡 Medium

---

# Screen 9 — Settings

## Purpose

Manage user and organization settings.

## Components

- Profile
- Organization
- Team Members
- Preferences

## APIs

GET /users/me

PUT /users/me

Priority

🟢 Low

---

# Global Components

Every screen includes:

- Navbar
- Sidebar
- Toast Notifications
- Loading Indicator
- Error Handler

---

# MVP Screen List

| Screen | Priority |
|----------|----------|
| Login | 🔴 High |
| Dashboard | 🔴 High |
| Projects | 🔴 High |
| Project Details | 🟡 Medium |
| Search | 🔴 High |
| AI Chat | 🔴 High |
| Timeline | 🟡 Medium |
| Integrations | 🟡 Medium |
| Settings | 🟢 Low |

---

# Navigation Flow

```
Login

↓

Dashboard

├── Projects
├── Search
├── AI Chat
├── Timeline
├── Integrations
└── Settings
```

---

# Definition of Done

A screen is considered complete when:

- UI implemented
- Connected to APIs
- Responsive
- Accessible
- Tested
- Matches Figma design