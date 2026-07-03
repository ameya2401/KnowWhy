from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class KnowledgeItemRead(BaseModel):
    id: UUID
    organization_id: UUID
    project_id: UUID
    source: str
    source_entity_id: str
    entity_type: str
    title: str
    description: str | None = None
    url: str | None = None
    author: str | None = None
    created_time: datetime
    updated_time: datetime
    tags: list[str] | None = None
    status: str

    model_config = {"from_attributes": True}


class KnowledgeItemDetail(KnowledgeItemRead):
    content: str | None = None
    metadata_json: dict | None = None

    model_config = {"from_attributes": True}


class KnowledgeRelationshipRead(BaseModel):
    id: UUID
    source_item_id: UUID
    target_item_id: UUID
    relationship_type: str
    confidence: float
    created_at: datetime

    # We will include basic properties of source/target items for detail rendering
    source_item: KnowledgeItemRead | None = None
    target_item: KnowledgeItemRead | None = None

    model_config = {"from_attributes": True}


class KnowledgeItemListResponse(BaseModel):
    items: list[KnowledgeItemRead]
    total: int


class KnowledgeSyncLogRead(BaseModel):
    id: UUID
    project_id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    items_synced: int
    relationships_created: int
    error_message: str | None = None

    model_config = {"from_attributes": True}
