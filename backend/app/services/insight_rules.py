from abc import ABC, abstractmethod
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import KnowledgeItem, KnowledgeRelationship


class InsightRule(ABC):
    """Base interface for Engineering Insight Detection Rules (Strategy Pattern)."""

    @abstractmethod
    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Analyzes knowledge items and returns lists of potential insights."""
        pass


class DocumentationGapRule(InsightRule):
    """Detects features/changes introduced in code (commits/PRs) that lack documentation."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Fetch commits and PRs
        stmt_code = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["commit", "pull_request"]),
            KnowledgeItem.status == "active",
        )
        res_code = await db.execute(stmt_code)
        code_items = res_code.scalars().all()

        # Fetch doc pages
        stmt_docs = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["notion_page", "document"]),
            KnowledgeItem.status == "active",
        )
        res_docs = await db.execute(stmt_docs)
        doc_items = res_docs.scalars().all()

        insights = []
        doc_titles_lower = [d.title.lower() for d in doc_items]

        # Key technology words to watch out for
        keywords = ["auth", "billing", "search", "database", "cache", "api", "security", "docker"]

        for keyword in keywords:
            # Check if keyword is in code items
            matching_code = [
                c
                for c in code_items
                if keyword in c.title.lower()
                or (c.description and keyword in c.description.lower())
            ]
            if not matching_code:
                continue

            # Check if keyword is in any doc page title
            has_doc = any(keyword in t for t in doc_titles_lower)
            if not has_doc:
                # We have a gap!
                insights.append(
                    {
                        "rule_name": "documentation_gap",
                        "severity": "warning",
                        "confidence": 0.85,
                        "title": f"Missing Documentation for '{keyword.capitalize()}' Feature",
                        "description": (
                            f"Recent code changes reference '{keyword}', but there are no "
                            f"corresponding Notion pages or Google Drive files found documenting this feature."
                        ),
                        "evidence_items": matching_code[:3],
                        "suggested_actions": [
                            f"Create a design specification page in Notion for the {keyword.capitalize()} module.",
                            f"Add architecture guidelines explaining how {keyword.capitalize()} is integrated.",
                        ],
                    }
                )

        return insights


class StaleKnowledgeRule(InsightRule):
    """Detects pages or documentation that haven't been updated for a long period."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Find docs updated more than 30 days ago
        cutoff = datetime.now(UTC) - timedelta(days=30)
        stmt = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["notion_page", "document"]),
            KnowledgeItem.updated_time < cutoff,
            KnowledgeItem.status == "active",
        )
        res = await db.execute(stmt)
        stale_items = res.scalars().all()

        insights = []
        if stale_items:
            for item in stale_items[:3]:  # Report top 3 stale items individually
                insights.append(
                    {
                        "rule_name": "stale_knowledge",
                        "severity": "suggestion",
                        "confidence": 0.75,
                        "title": f"Stale Documentation: '{item.title}'",
                        "description": (
                            f"The document '{item.title}' was last updated on "
                            f"{item.updated_time.strftime('%Y-%m-%d')}. It may contain outdated design patterns or APIs."
                        ),
                        "evidence_items": [item],
                        "suggested_actions": [
                            f"Review and update the content of '{item.title}'.",
                            "Archive the document if the feature has been deprecated.",
                        ],
                    }
                )
        return insights


class ArchitectureDriftRule(InsightRule):
    """Detects contradictions between architecture decisions and actual implementation."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Fetch architectural records (e.g. containing "decision", "architecture", "adr" in title)
        stmt_adr = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["notion_page", "document"]),
            KnowledgeItem.title.ilike("%decision%"),
            KnowledgeItem.status == "active",
        )
        res_adr = await db.execute(stmt_adr)
        adrs = res_adr.scalars().all()

        # Fetch recent commits/PRs
        stmt_code = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["commit", "pull_request"]),
            KnowledgeItem.status == "active",
        )
        res_code = await db.execute(stmt_code)
        code_items = res_code.scalars().all()

        insights = []
        # Check for database discrepancies (e.g. Postgres vs MySQL / Mongo)
        for adr in adrs:
            adr_content = (adr.content or "").lower() + adr.title.lower()
            if "postgresql" in adr_content or "postgres" in adr_content:
                # Look for MySQL/Mongo in commits
                drift_commits = [
                    c
                    for c in code_items
                    if "mysql" in c.title.lower() or "mongodb" in c.title.lower()
                ]
                if drift_commits:
                    insights.append(
                        {
                            "rule_name": "architecture_drift",
                            "severity": "critical",
                            "confidence": 0.90,
                            "title": "Architecture Drift: PostgreSQL DB Mandate Contradicted",
                            "description": (
                                f"Architectural decision '{adr.title}' specifies PostgreSQL, "
                                f"but recent code modifications reference alternate storage solutions (e.g., MySQL/MongoDB)."
                            ),
                            "evidence_items": [adr] + drift_commits[:2],
                            "suggested_actions": [
                                "Confirm whether MySQL/MongoDB usage aligns with current architecture guidelines.",
                                "Update the architectural decision record if the project has officially migrated databases.",
                            ],
                        }
                    )
            elif "mysql" in adr_content:
                drift_commits = [
                    c
                    for c in code_items
                    if "postgres" in c.title.lower() or "mongodb" in c.title.lower()
                ]
                if drift_commits:
                    insights.append(
                        {
                            "rule_name": "architecture_drift",
                            "severity": "critical",
                            "confidence": 0.90,
                            "title": "Architecture Drift: MySQL DB Mandate Contradicted",
                            "description": (
                                f"Architectural decision '{adr.title}' specifies MySQL, "
                                f"but recent code modifications reference alternate storage solutions (e.g., Postgres/MongoDB)."
                            ),
                            "evidence_items": [adr] + drift_commits[:2],
                            "suggested_actions": [
                                "Confirm whether PostgreSQL/MongoDB usage aligns with current architecture guidelines.",
                                "Update the architectural decision record if the project has officially migrated databases.",
                            ],
                        }
                    )
        return insights


class DuplicateKnowledgeRule(InsightRule):
    """Detects pages with highly similar titles or overlap content."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Fetch doc pages
        stmt = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["notion_page", "document"]),
            KnowledgeItem.status == "active",
        )
        res = await db.execute(stmt)
        docs = res.scalars().all()

        insights = []
        seen_pairs = set()

        for i, d1 in enumerate(docs):
            for j, d2 in enumerate(docs):
                if i >= j:
                    continue
                pair_key = tuple(sorted([str(d1.id), str(d2.id)]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Simple title similarity check
                t1 = d1.title.lower().strip()
                t2 = d2.title.lower().strip()
                if t1 == t2 or (len(t1) > 5 and len(t2) > 5 and (t1 in t2 or t2 in t1)):
                    insights.append(
                        {
                            "rule_name": "duplicate_knowledge",
                            "severity": "warning",
                            "confidence": 0.80,
                            "title": f"Duplicate Documentation Found: '{d1.title}' & '{d2.title}'",
                            "description": (
                                f"The documents '{d1.title}' and '{d2.title}' share highly similar titles "
                                f"and likely cover overlapping technical domains. Consolidating them will improve search indexing quality."
                            ),
                            "evidence_items": [d1, d2],
                            "suggested_actions": [
                                f"Merge the content of '{d2.title}' into '{d1.title}'.",
                                f"Delete or archive the duplicate page '{d2.title}'.",
                            ],
                        }
                    )
        return insights


class ProjectHealthRule(InsightRule):
    """Detects issues with repository health such as stale open PRs or unresolved issues."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Fetch PRs and Issues
        stmt = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["pull_request", "issue"]),
            KnowledgeItem.status == "active",
        )
        res = await db.execute(stmt)
        items = res.scalars().all()

        # Custom logic: if open issues count > 5, flag project health
        open_issues = []
        stale_prs = []

        for item in items:
            meta = item.metadata_json or {}
            state = meta.get("state", "").lower()
            if item.entity_type == "issue" and state in ["open", "active"]:
                open_issues.append(item)
            elif item.entity_type == "pull_request" and state in ["open", "draft"]:
                # Check if updated_time is older than 7 days
                if item.updated_time < datetime.now(UTC) - timedelta(days=7):
                    stale_prs.append(item)

        insights = []
        if len(open_issues) > 5:
            insights.append(
                {
                    "rule_name": "project_health",
                    "severity": "warning",
                    "confidence": 0.85,
                    "title": "Unresolved Issue Backlog Accumulating",
                    "description": (
                        f"The project currently has {len(open_issues)} open issues in the backlog. "
                        f"This could indicate bottlenecking or lack of focus on bugs."
                    ),
                    "evidence_items": open_issues[:5],
                    "suggested_actions": [
                        "Prioritize critical bugs in the upcoming planning cycle.",
                        "Close outdated issues that are no longer relevant to the codebase.",
                    ],
                }
            )

        if stale_prs:
            insights.append(
                {
                    "rule_name": "project_health",
                    "severity": "warning",
                    "confidence": 0.90,
                    "title": f"Stale Pull Requests Pending Review ({len(stale_prs)})",
                    "description": (
                        f"There are {len(stale_prs)} open pull requests that haven't been updated for over a week. "
                        f"Stale PRs delay features and increase merge conflict risks."
                    ),
                    "evidence_items": stale_prs[:3],
                    "suggested_actions": [
                        "Assign reviewers to the stale pull requests immediately.",
                        "Close or draft pull requests that are blocked indefinitely.",
                    ],
                }
            )

        return insights


class KnowledgeCoverageRule(InsightRule):
    """Detects areas with low knowledge coverage (e.g. connected GitHub repo but zero documentation pages)."""

    async def analyze(
        self, db: AsyncSession, project_id: UUID, organization_id: UUID
    ) -> List[Dict[str, Any]]:
        # Count code vs docs
        stmt_code = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["commit", "pull_request"]),
            KnowledgeItem.status == "active",
        )
        res_code = await db.execute(stmt_code)
        code_count = len(res_code.scalars().all())

        stmt_docs = select(KnowledgeItem).where(
            KnowledgeItem.project_id == project_id,
            KnowledgeItem.entity_type.in_(["notion_page", "document"]),
            KnowledgeItem.status == "active",
        )
        res_docs = await db.execute(stmt_docs)
        doc_count = len(res_docs.scalars().all())

        insights = []
        if code_count > 10 and doc_count == 0:
            insights.append(
                {
                    "rule_name": "knowledge_coverage",
                    "severity": "critical",
                    "confidence": 0.95,
                    "title": "Zero Documentation Coverage for Active Codebase",
                    "description": (
                        f"This project has active code integration ({code_count} commits/PRs), "
                        f"but zero documentation pages (Notion/Google Drive files) are connected. "
                        f"This creates a critical single-point-of-failure risk."
                    ),
                    "evidence_items": [],
                    "suggested_actions": [
                        "Connect a Notion workspace containing setup and API documentation.",
                        "Import existing architectural guides or user guides into Google Drive.",
                    ],
                }
            )
        elif code_count > 10 and doc_count < 3:
            insights.append(
                {
                    "rule_name": "knowledge_coverage",
                    "severity": "warning",
                    "confidence": 0.80,
                    "title": "Low Documentation Coverage",
                    "description": (
                        f"This project has active code integration ({code_count} commits/PRs), "
                        f"but only {doc_count} documentation pages connected. Increasing document coverage helps AI assistant accuracy."
                    ),
                    "evidence_items": [],
                    "suggested_actions": [
                        "Review key features and document them in Notion.",
                        "Link technical designs to the search repository.",
                    ],
                }
            )
        return insights


# Aggregate all default rules
ALL_RULES = [
    DocumentationGapRule(),
    StaleKnowledgeRule(),
    ArchitectureDriftRule(),
    DuplicateKnowledgeRule(),
    ProjectHealthRule(),
    KnowledgeCoverageRule(),
]
