# Design System

Version: 1.0

Status: Final (MVP)

---

# Purpose

This document defines the visual language of KnowWhy.

Every screen and component should follow these standards to ensure a consistent user experience.

---

# Design Principles

- Simple
- Consistent
- Accessible
- Responsive
- Developer Friendly

Every UI component should feel like it belongs to the same application.

---

# Design Tokens

## Border Radius

Small

```
6px
```

Medium

```
10px
```

Large

```
16px
```

---

## Spacing

Use an 8-point grid.

```
4px

8px

16px

24px

32px

48px

64px
```

Avoid arbitrary spacing.

---

## Shadows

Small

Cards

Medium

Dropdowns

Large

Modals

Use shadows subtly.

---

# Colors

## Primary

Blue

Used for:

- Primary buttons
- Links
- Active navigation
- Focus states

---

## Secondary

Gray

Used for:

- Borders
- Backgrounds
- Disabled elements

---

## Success

Green

Used for:

- Success messages
- Completed status

---

## Warning

Orange

Used for:

- Pending actions
- Warnings

---

## Error

Red

Used for:

- Errors
- Validation
- Destructive actions

---

# Typography

Primary Font

Inter

---

## Heading Sizes

H1

32px

H2

24px

H3

20px

H4

18px

---

## Body Text

Normal

16px

Small

14px

Caption

12px

---

# Icons

Use:

Lucide React

Guidelines

- Keep icon size consistent
- Pair icons with labels where possible
- Avoid decorative icons

---

# Buttons

## Primary Button

Purpose

Main action

Example

```
Create Project
```

---

## Secondary Button

Purpose

Alternative action

Example

```
Cancel
```

---

## Danger Button

Purpose

Delete

Reset

Remove

---

## Icon Button

Purpose

Quick actions

Example

Search

Settings

Refresh

---

# Inputs

Standard text input

Should include

- Label
- Placeholder
- Validation
- Error message

---

# Search Bar

The search bar is a primary component.

Features

- Search icon
- Placeholder
- Clear button
- Keyboard shortcut hint

---

# Cards

Cards display grouped information.

Examples

Project Card

Decision Card

Document Card

Meeting Card

Each card should contain:

- Title
- Metadata
- Actions
- Status

---

# Tables

Use tables for structured information.

Include:

- Sorting
- Pagination
- Search
- Empty state

---

# Modals

Use for:

- Confirmations
- Creating entities
- Editing entities

Avoid using modals for long workflows.

---

# Sidebar

Contains

- Logo
- Navigation
- Workspace Selector
- User Profile

Should remain fixed.

---

# Navbar

Contains

- Search
- Notifications
- User Menu

Should remain visible while scrolling.

---

# Dashboard Widgets

Examples

- Recent Projects
- Recent Activity
- AI Insights
- Pending Tasks
- Connected Integrations

Widgets should be modular.

---

# Status Badges

Examples

Active

Pending

Completed

Failed

Archived

Use consistent colors.

---

# Loading States

Use

- Skeleton Loaders
- Progress Indicators

Avoid blank pages.

---

# Empty States

Every empty page should include:

- Illustration (optional)
- Short message
- Primary action

Example

"No integrations connected yet."

Button

"Connect GitHub"

---

# Notifications

Use toast notifications.

Types

- Success
- Error
- Warning
- Info

Duration

3–5 seconds

---

# Responsive Breakpoints

Mobile

<768px

Tablet

768–1024px

Desktop

>1024px

MVP focuses on desktop.

---

# Component Naming

Examples

```
Button.tsx

SearchBar.tsx

ProjectCard.tsx

TimelineItem.tsx

UserAvatar.tsx
```

Keep names descriptive.

---

# Reusable Components

Build once.

Reuse everywhere.

Examples

- Button
- Input
- Card
- Modal
- Badge
- Avatar
- Dropdown
- Search Bar
- Timeline Item
- Loading Skeleton

---

# Do's

- Keep layouts clean.
- Maintain consistent spacing.
- Use reusable components.
- Show loading and error states.
- Prioritize readability.

---

# Don'ts

- Don't mix button styles.
- Don't use random colors.
- Don't overload pages.
- Don't create duplicate components.
- Don't hide important actions.

---

# Summary

The Design System ensures that KnowWhy maintains a professional, consistent, and scalable interface.

Every new component should follow these guidelines before implementation.