export interface EvidenceItem {
  id?: string;
  title: string;
  entity_type: string;
  url?: string;
}

export interface EngineeringInsight {
  id: string;
  project_id: string;
  organization_id: string;
  title: string;
  description: string;
  insight_type: string;
  severity: "critical" | "warning" | "suggestion";
  confidence: number;
  evidence: EvidenceItem[] | null;
  suggested_actions: string[] | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SeverityBreakdown {
  critical: number;
  warning: number;
  suggestion: number;
}

export interface InsightTypeBreakdown {
  documentation_gap: number;
  stale_knowledge: number;
  architecture_drift: number;
  duplicate_knowledge: number;
  project_health: number;
  knowledge_coverage: number;
}

export interface EngineeringInsightStatistics {
  total_insights: number;
  severity_breakdown: SeverityBreakdown;
  type_breakdown: InsightTypeBreakdown;
  average_confidence: number;
}
