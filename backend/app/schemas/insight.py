from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    id: UUID | None = None
    title: str
    entity_type: str
    url: str | None = None


class EngineeringInsightRead(BaseModel):
    id: UUID
    project_id: UUID
    organization_id: UUID
    title: str
    description: str
    insight_type: str
    severity: str
    confidence: float
    evidence: list[EvidenceItem] | None = None
    suggested_actions: list[str] | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EngineeringInsightAnalyzeRequest(BaseModel):
    project_id: UUID


class SeverityBreakdown(BaseModel):
    critical: int = 0
    warning: int = 0
    suggestion: int = 0


class InsightTypeBreakdown(BaseModel):
    documentation_gap: int = 0
    stale_knowledge: int = 0
    architecture_drift: int = 0
    duplicate_knowledge: int = 0
    project_health: int = 0
    knowledge_coverage: int = 0


class EngineeringInsightStatistics(BaseModel):
    total_insights: int
    severity_breakdown: SeverityBreakdown
    type_breakdown: InsightTypeBreakdown
    average_confidence: float
