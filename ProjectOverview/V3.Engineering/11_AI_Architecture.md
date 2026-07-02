# AI Architecture

Version: 1.0

Status: Draft

Authors:
- Ameya Bhagat
- Project Partner

---

# Purpose

This document defines the Artificial Intelligence architecture of KnowWhy.

Unlike many AI-powered products, KnowWhy is **not** built around a single Large Language Model (LLM).

Instead, KnowWhy follows a layered intelligence architecture in which multiple AI and Machine Learning components collaborate to understand organizational context, construct memory, reason over evidence, and assist users.

The objective of this document is to explain:

- Why AI is required.
- Where AI is required.
- Where AI is deliberately NOT used.
- How AI interacts with organizational memory.
- How AI decisions remain explainable.
- How AI evolves over time.

---

# Philosophy

KnowWhy is **not** an AI product.

KnowWhy is an Organizational Intelligence Platform.

Artificial Intelligence is one capability that enables organizational intelligence.

Memory remains the primary product.

AI consumes memory.

AI enriches memory.

AI reasons over memory.

AI never replaces memory.

---

# Fundamental Principle

Traditional AI Systems

```
Question

↓

LLM

↓

Answer
```

KnowWhy

```
Question

↓

Memory Retrieval

↓

Evidence Collection

↓

Relationship Analysis

↓

Reasoning

↓

LLM

↓

Evidence Verification

↓

Answer
```

The LLM is intentionally placed near the end of the pipeline.

The LLM never becomes the system of record.

---

# Why We Are NOT Training Our Own LLM

Training a foundation model requires:

- Massive datasets
- Thousands of GPUs
- Significant financial resources
- Continuous retraining
- Dedicated ML infrastructure

These requirements are incompatible with:

- a startup,
- a student project,
- and the actual problem KnowWhy attempts to solve.

KnowWhy therefore focuses on applying AI effectively rather than reproducing existing foundation models.

---

# AI Responsibilities

AI inside KnowWhy performs six primary responsibilities.

---

## Responsibility 1

Information Understanding

Examples

Email

↓

Intent

Slack Message

↓

Topic

Meeting Transcript

↓

Summary

PR Discussion

↓

Decision

Documents

↓

Structured Knowledge

---

## Responsibility 2

Knowledge Extraction

Raw information is converted into structured entities.

Example

Input

"We decided to migrate authentication to OAuth."

Output

Decision

Migration

Authentication

OAuth

Evidence

Confidence

Participants

This process transforms language into knowledge.

---

## Responsibility 3

Relationship Discovery

AI identifies hidden relationships.

Examples

Developer

↓

Frequently Reviews

↓

Authentication PRs

Meeting

↓

Discussed

↓

Architecture Decision

Issue

↓

Caused

↓

Hotfix

Relationships become part of organizational memory.

---

## Responsibility 4

Reasoning

AI reasons over existing memory.

Examples

Why was Redis adopted?

Has this happened before?

Who should review this?

Which document explains this?

What changed after Release 3?

Reasoning always operates on retrieved context.

---

## Responsibility 5

Recommendation

KnowWhy suggests

Experts

Relevant documents

Previous implementations

Duplicate work

Missing documentation

Potential risks

Recommendations remain advisory.

---

## Responsibility 6

Continuous Learning

KnowWhy continuously improves:

Entity extraction.

Relationship discovery.

Workflow prediction.

Search ranking.

Confidence estimation.

AI quality improves as organizational memory grows.

---

# AI Pipeline

Every AI request follows the same architecture.

```
User Question

↓

Authentication

↓

Permission Check

↓

Context Retrieval

↓

Evidence Retrieval

↓

Relationship Expansion

↓

Prompt Construction

↓

LLM

↓

Verification

↓

Confidence Estimation

↓

Response Generation

↓

Logging
```

Every stage exists for a reason.

No stage should be skipped.

---

# AI Components

KnowWhy consists of multiple AI components.

No single model performs every task.

---

## Component 1

Embedding Model

Purpose

Convert organizational content into vectors.

Used for

Semantic Search.

Context Retrieval.

Similarity Search.

Duplicate Detection.

Possible Models

BGE

E5

OpenAI Embeddings

Jina Embeddings

Instructor

---

## Component 2

Large Language Model

Purpose

Language understanding.

Reasoning.

Question answering.

Summarization.

Examples

GPT

Claude

Gemini

Llama

Qwen

LLMs should never permanently store organizational knowledge.

---

## Component 3

RAG Engine

Purpose

Retrieve organizational evidence before reasoning.

Without RAG

LLM Hallucinates.

With RAG

LLM reasons using organizational evidence.

---

## Component 4

Memory Builder

Purpose

Construct organizational memory.

Input

Events

Output

Connected organizational graph.

---

## Component 5

Relationship Extractor

Purpose

Discover relationships between entities.

Examples

Developer

↓

Worked On

↓

Repository

Decision

↓

Influenced

↓

Architecture

Meeting

↓

Produced

↓

Task

---

## Component 6

Confidence Engine

Purpose

Estimate confidence.

Confidence depends on:

Evidence quantity.

Evidence quality.

Relationship strength.

Source agreement.

Time.

Model certainty.

---

## Component 7

Recommendation Engine

Purpose

Generate organizational recommendations.

Examples

Experts.

Related documents.

Previous discussions.

Workflow suggestions.

---

# Small Machine Learning Models

KnowWhy intentionally separates:

Large Language Models

from

Task Specific Models.

Examples

Email Classifier

Issue Categorizer

Priority Prediction

Duplicate Detection

Reviewer Recommendation

Workflow Prediction

Risk Prediction

These models are lightweight.

Easy to retrain.

Explainable.

Fast.

Ideal for research.

---

# Why Train Small Models?

Small models provide:

Lower inference cost.

Higher explainability.

Better domain specialization.

Offline capability.

Research opportunities.

Educational value.

They also align with KnowWhy' long-term vision of gradually replacing generic AI components with domain-specific intelligence.

---

# AI Safety

KnowWhy follows strict safety principles.

AI should:

Never fabricate evidence.

Never hide uncertainty.

Never bypass permissions.

Never execute destructive actions autonomously.

Never expose private organizational information.

Every recommendation should remain explainable.

---

# Human-in-the-Loop

High-impact actions require approval.

Examples

Deleting data.

Updating production systems.

Executing workflows.

Changing permissions.

Sending customer emails.

AI may recommend.

Humans approve.

---

# Model Independence

KnowWhy must never depend on one AI provider.

Requirements

Replace OpenAI.

Replace Claude.

Replace Gemini.

Replace local models.

Without redesigning business logic.

The AI abstraction layer isolates provider-specific logic.

---

# Cost Optimization

LLMs are expensive.

KnowWhy should optimize costs.

Strategies

Context compression.

Prompt caching.

Response caching.

Smaller models first.

Escalation only when necessary.

Batch inference.

Embedding reuse.

Model routing.

---

# Evaluation Metrics

Every AI component should be measurable.

Metrics

Precision.

Recall.

Latency.

Hallucination Rate.

Context Accuracy.

Retrieval Accuracy.

Recommendation Accuracy.

User Satisfaction.

Confidence Calibration.

Token Cost.

---

# Research Opportunities

KnowWhy enables research in:

Organizational Memory.

Enterprise RAG.

Knowledge Graph Reasoning.

Workflow Prediction.

Explainable AI.

Context Retrieval.

Decision Intelligence.

Human-AI Collaboration.

Hybrid AI Systems.

Each subsystem may later become an independent research publication.

---

# AI Evolution Roadmap

Version 1

LLM + RAG

Version 2

Relationship Learning

Version 3

Recommendation Models

Version 4

Workflow Prediction

Version 5

Agent Collaboration

Version 6

Domain Specific ML Models

Version 7

Adaptive Organizational Intelligence

AI capability should evolve incrementally.

Never all at once.

---

# Closing Statement

Artificial Intelligence is not the foundation of KnowWhy.

Organizational Memory is.

AI exists to understand, enrich, retrieve, reason over, and explain that memory.

If organizational memory is weak, AI cannot compensate.

If organizational memory is strong, even simple AI models become significantly more valuable.

Therefore, every future AI enhancement should first ask one question:

"Does this improve the organization's ability to remember, understand, and reason about its own work?"

If the answer is no, the enhancement does not belong in KnowWhy.