export interface EmbeddingQueueStatus {
  project_id: string;
  status: "idle" | "running" | "paused" | "completed" | "failed";
  total_items: number;
  processed_items: number;
  failed_items: number;
  last_index_time: string | null;
  error_message: string | null;
}

export interface EmbeddingStatistics {
  total_vectors: number;
  indexed_documents: number;
  queue_size: number;
  failed_jobs: number;
}
