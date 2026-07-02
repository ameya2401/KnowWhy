# Problem Discovery

Version: 0.1

Status: Draft

Authors:
- Ameya Bhagat
- Project Partner

---

# Purpose of this Document

Before designing software, selecting technologies, or writing a single line of code, it is essential to understand the problem that justifies the existence of the product.

This document records the reasoning process that led to the selection of the problem statement.

It captures the motivations, assumptions, rejected ideas, observations, research findings, and hypotheses that collectively shaped the direction of KnowWhy.

Unlike a traditional college project report, this document is intended to preserve the evolution of our thinking.

Future decisions should always be traceable back to this document.

---

# The Original Motivation

The project did not begin with a technology.

It began with a question.

> "Can we build one software product that is genuinely useful, technically challenging, academically valuable, commercially viable, and capable of teaching us nearly every major area of Computer Science?"

This question became the foundation of the project.

The objective was never to build another college assignment.

The objective was to build something we would still be proud of five years after graduation.

---

# Personal Goals

The project should simultaneously satisfy multiple objectives.

## Learning

The project should expose us to:

- Backend Development
- Frontend Development
- Artificial Intelligence
- Machine Learning
- Databases
- Distributed Systems
- Cloud Computing
- DevOps
- Security
- System Design
- Product Design
- Research Methodology

Rather than learning these topics independently, the project should naturally require them.

---

## Placements

The project should become the strongest item in our portfolio.

It should demonstrate:

- engineering maturity
- architectural thinking
- problem solving
- research capability
- software craftsmanship

Rather than simply showing technical skills, it should demonstrate the ability to solve complex real-world problems.

---

## Research

The project should support future academic research.

Every major subsystem should ideally answer one or more research questions.

This allows the project to evolve into:

- a final-year research paper,
- multiple experiments,
- and potentially future publications.

---

## Startup Potential

The project should not be restricted to academic requirements.

It should solve a problem that organizations would willingly pay to solve.

If real users adopt the platform, it should have the potential to evolve into a commercial software product.

---

# The Initial Exploration

The research process intentionally avoided beginning with product ideas.

Instead, it focused on discovering problems.

Research was conducted across multiple sources including:

- Reddit
- GitHub Issues
- GitHub Discussions
- Hacker News
- Stack Overflow
- Product Hunt
- Developer Communities
- Research Papers
- Startup Discussions
- Technical Blogs
- Open Source Communities

The objective was not to discover interesting technologies.

The objective was to discover recurring frustration.

---

# Important Observation

One recurring pattern appeared repeatedly.

People rarely complain about lacking software.

Instead, they complain about software not working together.

Examples included:

- Copying information between applications.
- Maintaining duplicate records.
- Losing important context.
- Searching across disconnected tools.
- Repeating manual workflows.
- Remembering previous decisions.
- Switching between multiple platforms throughout the day.

These problems appeared across industries.

The specific software changed.

The workflow pain remained remarkably similar.

---

# The Real Problem

Initially, we believed the problem was automation.

After further discussion, that assumption was challenged.

Automation already exists.

Products such as Zapier, Make, n8n, and Workato demonstrate that connecting software is no longer the primary challenge.

The deeper problem is context.

Software stores information.

Very little software understands relationships.

Organizations remember data.

They frequently forget knowledge.

This distinction became the turning point of the project.

---

# Context vs Information

Information answers:

"What happened?"

Context answers:

"Why did it happen?"

Example:

A spreadsheet may contain an updated delivery date.

The context includes:

- which email caused the change,
- who approved it,
- which meeting discussed it,
- which customer requested it,
- what alternatives were considered,
- and what consequences resulted.

Current software generally stores the outcome.

It rarely preserves the reasoning.

---

# Evolution of the Core Idea

The project evolved through several stages.

## Stage 1

Workflow Automation

Question:

Can repetitive work be automated?

Observation:

Yes.

Existing products already solve much of this problem.

Result:

Not sufficiently differentiated.

---

## Stage 2

AI Workflow Automation

Question:

Can LLMs improve automation?

Observation:

Yes.

However, many companies are already exploring AI-driven workflow automation.

Result:

Interesting but insufficiently unique.

---

## Stage 3

Organizational Memory

Question:

Can software remember work instead of simply storing files?

Observation:

This problem appears significantly less mature.

Few systems maintain persistent organizational memory across multiple software platforms.

Result:

Promising.

---

## Stage 4

Context-Aware Decision Support

Question:

Can organizational memory improve decision making?

Observation:

Decisions become significantly more accurate when historical organizational context is available.

Result:

This became the current research direction.

---

# Why Existing Software Is Not Enough

Existing software generally focuses on one domain.

Examples include:

Email.

Project management.

Documentation.

Messaging.

CRM.

ERP.

Knowledge management.

Automation.

Each category performs its individual function well.

The difficulty begins when work spans multiple systems.

Organizations rarely operate inside a single application.

Consequently:

- knowledge becomes fragmented,
- context disappears,
- duplicate work increases,
- and organizational memory slowly degrades.

---

# Questions That Shaped the Project

Throughout the discovery phase, several questions repeatedly guided our thinking.

Why do organizations lose knowledge despite using dozens of software products?

Why are employees still copying information manually?

Why are important decisions difficult to reconstruct months later?

Why do automation platforms require users to explicitly define every rule?

Can software understand work rather than merely executing predefined instructions?

Can AI become a reasoning layer instead of simply generating text?

Can persistent memory improve decision making?

Could explainable AI increase organizational trust?

Could this become both a startup and a research project?

---

# Assumptions

At the current stage, several assumptions remain unvalidated.

Assumption 1

Organizations experience measurable productivity loss because organizational context is fragmented.

Status:

Requires validation.

---

Assumption 2

Persistent organizational memory improves workflow quality.

Status:

Requires experimentation.

---

Assumption 3

Users are willing to trust AI recommendations when explanations are provided.

Status:

Requires user studies.

---

Assumption 4

Current workflow platforms do not adequately preserve organizational context.

Status:

Requires competitive evaluation.

---

# Success Criteria for the Discovery Phase

The discovery phase will be considered complete only when the following questions have been answered using evidence rather than intuition.

Who experiences this problem?

How frequently does it occur?

How expensive is the problem?

What solutions currently exist?

Where do those solutions fail?

Why do users tolerate existing limitations?

What differentiates our approach?

Why is this the correct problem to solve?

---

# Open Questions

The following questions intentionally remain unanswered.

They will guide the next stages of KnowWhy.

How should organizational memory be represented?

Should memory rely on vector databases, knowledge graphs, relational databases, or a hybrid approach?

How should AI reason over historical context?

What level of automation is appropriate?

How should user trust be maintained?

How should conflicting information be resolved?

How should privacy and security be enforced?

Which industries should be targeted first?

What constitutes an effective MVP?

---

# Closing Statement

Problem discovery is not a phase that ends once development begins.

It is a continuous process.

Every feature implemented throughout KnowWhy should strengthen the original problem statement rather than drift away from it.

The quality of the final product will ultimately depend less on the sophistication of its technology and more on the correctness of the problem it chooses to solve.

This document therefore serves as the intellectual foundation upon which every future design decision will be built.