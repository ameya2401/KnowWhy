import logging
import json
from uuid import UUID
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.insight import EngineeringInsight
from app.models.knowledge import KnowledgeItem
from app.services.insight_rules import ALL_RULES
from app.services.llm_providers import get_llm_provider

logger = logging.getLogger(__name__)


class InsightService:
    """Manages detection, AI refinement, persistence, and querying of Engineering Insights."""

    @staticmethod
    async def analyze_project_insights(
        db: AsyncSession, project_id: UUID, organization_id: UUID, provider_override: Optional[str] = None
    ) -> List[EngineeringInsight]:
        """Triggers proactive analysis, runs all rules, refines with LLM, and persists results."""
        logger.info(f"Starting engineering intelligence analysis for project {project_id}")

        # 1. Run all rule strategies
        candidates = []
        for rule in ALL_RULES:
            try:
                findings = await rule.analyze(db, project_id, organization_id)
                candidates.extend(findings)
            except Exception as e:
                logger.error(f"Rule {rule.__class__.__name__} failed during analysis: {e}", exc_info=True)

        # 2. Get LLM provider for refinement
        llm = get_llm_provider(provider_override)

        processed_insights: List[EngineeringInsight] = []

        # 3. Process each candidate
        for candidate in candidates:
            # Prepare evidence payload for storing in DB
            evidence_payload = []
            evidence_context_str = ""
            for item in candidate.get("evidence_items", []):
                evidence_payload.append({
                    "id": str(item.id),
                    "title": item.title,
                    "entity_type": item.entity_type,
                    "url": item.url
                })
                evidence_context_str += f"- [{item.entity_type.upper()}] {item.title}: {item.content or item.description or ''}\n"

            # Use LLM to refine the candidate title/description/suggested actions
            prompt = (
                f"You are the KnowWhy Engineering Advisor.\n"
                f"Analyze the following potential engineering issue identified in our workspace:\n"
                f"Candidate Title: {candidate['title']}\n"
                f"Type: {candidate['rule_name']}\n"
                f"Initial Severity: {candidate['severity']}\n"
                f"Initial Description: {candidate['description']}\n\n"
                f"Supporting Evidence Context:\n{evidence_context_str}\n"
                f"Refine this into a high-quality, actionable, and accurate engineering insight.\n"
                f"Provide your response in JSON format containing the following keys:\n"
                f"- 'title': Refined user-friendly title\n"
                f"- 'description': Clear explanation of the risk, why it matters, and why it was flagged.\n"
                f"- 'severity': 'critical', 'warning', or 'suggestion'\n"
                f"- 'confidence': Float value between 0.0 and 1.0 representing your confidence.\n"
                f"- 'suggested_actions': A list of specific, concrete steps to resolve the issue.\n"
            )

            refined_data = {}
            try:
                response = await llm.generate_response(
                    prompt=prompt,
                    system_prompt="You are a professional engineering manager and software architect advisor.",
                    temperature=0.2
                )
                text = response.get("text", "")
                # Try to extract JSON
                json_match = None
                # Simple extraction in case LLM wraps it in markdown blocks
                if "```json" in text:
                    parts = text.split("```json")
                    if len(parts) > 1:
                        json_match = parts[1].split("```")[0].strip()
                elif "```" in text:
                    parts = text.split("```")
                    if len(parts) > 1:
                        json_match = parts[1].strip()
                else:
                    json_match = text.strip()

                if json_match:
                    refined_data = json.loads(json_match)
            except Exception as e:
                logger.error(f"LLM refinement failed for candidate {candidate['title']}: {e}")

            # Fallback to rule candidate if LLM fails or doesn't return correct fields
            title = refined_data.get("title") or candidate["title"]
            description = refined_data.get("description") or candidate["description"]
            severity = refined_data.get("severity") or candidate["severity"]
            confidence = refined_data.get("confidence") or candidate["confidence"]
            suggested_actions = refined_data.get("suggested_actions") or candidate["suggested_actions"]

            if severity not in ["critical", "warning", "suggestion"]:
                severity = candidate["severity"]

            try:
                confidence = float(confidence)
            except ValueError:
                confidence = candidate["confidence"]

            # 4. Save to DB (Upsert pattern to avoid duplicates)
            # Find if there is an existing insight with same project_id, type and title
            stmt = select(EngineeringInsight).where(
                EngineeringInsight.project_id == project_id,
                EngineeringInsight.insight_type == candidate["rule_name"],
                EngineeringInsight.title == title,
                EngineeringInsight.status == "active"
            )
            res = await db.execute(stmt)
            existing = res.scalars().first()

            if existing:
                existing.description = description
                existing.severity = severity
                existing.confidence = confidence
                existing.evidence = evidence_payload
                existing.suggested_actions = suggested_actions
                existing.updated_at = datetime.now(UTC)
                insight_obj = existing
            else:
                insight_obj = EngineeringInsight(
                    project_id=project_id,
                    organization_id=organization_id,
                    title=title,
                    description=description,
                    insight_type=candidate["rule_name"],
                    severity=severity,
                    confidence=confidence,
                    evidence=evidence_payload,
                    suggested_actions=suggested_actions,
                    status="active"
                )
                db.add(insight_obj)

            processed_insights.append(insight_obj)

        await db.commit()

        # Reload objects from DB to populate IDs and datetimes
        output = []
        for p_in in processed_insights:
            stmt = select(EngineeringInsight).where(EngineeringInsight.id == p_in.id)
            res = await db.execute(stmt)
            obj = res.scalars().first()
            if obj:
                output.append(obj)

        return output

    @staticmethod
    async def list_project_insights(
        db: AsyncSession,
        project_id: UUID,
        organization_id: UUID,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        insight_type: Optional[str] = None
    ) -> List[EngineeringInsight]:
        """Lists engineering insights for a project with optional filters."""
        stmt = select(EngineeringInsight).where(
            EngineeringInsight.project_id == project_id,
            EngineeringInsight.organization_id == organization_id
        )

        if status:
            stmt = stmt.where(EngineeringInsight.status == status)
        if severity:
            stmt = stmt.where(EngineeringInsight.severity == severity)
        if insight_type:
            stmt = stmt.where(EngineeringInsight.insight_type == insight_type)

        # Ordering by severity (critical > warning > suggestion), confidence descending, freshness descending
        # Let's order by severity mapping and confidence.
        # We will sort it in python for complex severity ordering or use simple order_by in sql first
        stmt = stmt.order_by(EngineeringInsight.confidence.desc(), EngineeringInsight.created_at.desc())
        res = await db.execute(stmt)
        insights = list(res.scalars().all())

        # Sort python-side to guarantee severity priority: critical > warning > suggestion
        severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
        insights.sort(key=lambda x: (severity_order.get(x.severity, 3), -x.confidence))

        return insights

    @staticmethod
    async def get_insight_by_id(
        db: AsyncSession,
        insight_id: UUID,
        project_id: UUID,
        organization_id: UUID
    ) -> Optional[EngineeringInsight]:
        """Gets a single insight by ID with validation checks."""
        stmt = select(EngineeringInsight).where(
            EngineeringInsight.id == insight_id,
            EngineeringInsight.project_id == project_id,
            EngineeringInsight.organization_id == organization_id
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    @staticmethod
    async def get_insight_statistics(
        db: AsyncSession,
        project_id: UUID,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Generates statistical breakdown of active insights in the project."""
        stmt = select(EngineeringInsight).where(
            EngineeringInsight.project_id == project_id,
            EngineeringInsight.organization_id == organization_id,
            EngineeringInsight.status == "active"
        )
        res = await db.execute(stmt)
        insights = res.scalars().all()

        total = len(insights)
        sev_counts = {"critical": 0, "warning": 0, "suggestion": 0}
        type_counts = {
            "documentation_gap": 0,
            "stale_knowledge": 0,
            "architecture_drift": 0,
            "duplicate_knowledge": 0,
            "project_health": 0,
            "knowledge_coverage": 0
        }
        total_conf = 0.0

        for ins in insights:
            if ins.severity in sev_counts:
                sev_counts[ins.severity] += 1
            if ins.insight_type in type_counts:
                type_counts[ins.insight_type] += 1
            total_conf += ins.confidence

        avg_conf = total_conf / total if total > 0 else 0.0

        return {
            "total_insights": total,
            "severity_breakdown": sev_counts,
            "type_breakdown": type_counts,
            "average_confidence": round(avg_conf, 2)
        }
