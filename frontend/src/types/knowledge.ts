export interface KnowledgeItem {
  id: string;
  organization_id: string;
  project_id: string;
  source: "github" | "notion" | "google_drive" | string;
  source_entity_id: string;
  entity_type: "commit" | "pull_request" | "issue" | "notion_page" | "document" | "folder" | string;
  title: string;
  description: string | null;
  content?: string | null;
  url: string | null;
  author: string | null;
  created_time: string;
  updated_time: string;
  tags: string[] | null;
  status: string;
  metadata_json?: Record<string, any> | null;
}

export interface KnowledgeRelationship {
  id: string;
  source_item_id: string;
  target_item_id: string;
  relationship_type: string;
  confidence: number;
  created_at: string;
  source_item?: KnowledgeItem;
  target_item?: KnowledgeItem;
}

export interface KnowledgeSyncLog {
  id: string;
  project_id: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "completed" | "failed";
  items_synced: number;
  relationships_created: number;
  error_message: string | null;
}

export interface KnowledgeItemListResponse {
  items: KnowledgeItem[];
  total: number;
}
