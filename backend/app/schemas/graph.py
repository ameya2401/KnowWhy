from datetime import datetime

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    type: str  # "project", "user", "repository", "commit", "pull_request", "issue", "document", "notion_page", "decision", "meeting", "integration"  # noqa: E501
    title: str
    subtitle: str | None = None
    url: str | None = None
    author: str | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # "created", "references", "depends_on", "implements", "documents", "resolves", "updates", "discusses", "approves", "links_to", "contains"  # noqa: E501
    confidence: float = 1.0
    metadata_json: dict | None = Field(default=None, alias="metadata")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class NeighborInfo(BaseModel):
    id: str
    type: str
    title: str


class EntityRelationshipDetail(BaseModel):
    neighbor: NeighborInfo
    edge_type: str
    direction: str  # "incoming" or "outgoing"
    confidence: float = 1.0
    metadata_json: dict | None = Field(default=None, alias="metadata")

    model_config = {
        "populate_by_name": True
    }


class EntityDetailResponse(BaseModel):
    entity: GraphNode
    relationships: list[EntityRelationshipDetail]


class TimelineEvent(BaseModel):
    id: str
    type: str  # "commit", "pull_request", "issue", "notion_page", "document", "ai_conversation", "milestone"  # noqa: E501
    title: str
    description: str | None = None
    time: datetime
    author: str | None = None
    url: str | None = None
    metadata_json: dict | None = Field(default=None, alias="metadata")

    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class TimelineResponse(BaseModel):
    events: list[TimelineEvent]
