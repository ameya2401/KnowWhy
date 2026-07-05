export interface GraphNode {
  id: string;
  type:
    | "project"
    | "user"
    | "repository"
    | "commit"
    | "pull_request"
    | "issue"
    | "document"
    | "notion_page"
    | "decision"
    | "meeting"
    | "integration"
    | string;
  title: string;
  subtitle?: string;
  url?: string | null;
  author?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  confidence: number;
  metadata?: Record<string, unknown> | null;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface NeighborInfo {
  id: string;
  type: string;
  title: string;
}

export interface EntityRelationshipDetail {
  neighbor: NeighborInfo;
  edge_type: string;
  direction: "incoming" | "outgoing";
  confidence: number;
  metadata?: Record<string, unknown> | null;
}

export interface EntityDetailResponse {
  entity: GraphNode;
  relationships: EntityRelationshipDetail[];
}

export interface TimelineEvent {
  id: string;
  type:
    | "commit"
    | "pull_request"
    | "issue"
    | "notion_page"
    | "document"
    | "ai_conversation"
    | "milestone"
    | string;
  title: string;
  description?: string | null;
  time: string;
  author?: string | null;
  url?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface TimelineResponse {
  events: TimelineEvent[];
}
