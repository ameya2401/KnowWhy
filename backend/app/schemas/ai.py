from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field


class AIQueryRequest(BaseModel):
    project_id: UUID
    q: str = Field(..., min_length=1, description="The user question to process")
    provider: str | None = Field(default=None, description="Force a specific LLM provider (openai, anthropic, gemini)")


class AIExplainRequest(BaseModel):
    project_id: UUID
    concept: str = Field(..., min_length=1, description="The concept or entity name to explain")
    provider: str | None = Field(default=None, description="Force a specific LLM provider (openai, anthropic, gemini)")


class AICitation(BaseModel):
    knowledge_item_id: UUID
    title: str
    source: str  # e.g., github, notion, drive
    url: str | None = None
    updated_at: datetime


class AIQueryResponse(BaseModel):
    answer: str
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Estimated confidence based on evidence agreement")
    sources: List[AICitation]
    related_knowledge: List[UUID] = Field(default_factory=list, description="IDs of related knowledge items")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Suggestions for further investigation")


class LLMProviderInfo(BaseModel):
    id: str
    name: str
    is_active: bool
    is_available: bool


class AIProvidersResponse(BaseModel):
    providers: List[LLMProviderInfo]
    active_provider: str


class AIStatisticsResponse(BaseModel):
    total_requests: int
    average_latency_ms: float
    total_tokens_used: int
    average_confidence: float


class AIConversationCreate(BaseModel):
    project_id: UUID
    title: str | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    citation_mode: str | None = None
    streaming_on: bool | None = None


class AIChatRequest(BaseModel):
    project_id: UUID
    message: str = Field(..., min_length=1)
    conversation_id: UUID | None = None
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    citation_mode: str | None = None
    streaming_on: bool | None = None


class AIMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    metadata: dict | None = None

    class Config:
        from_attributes = True


class AIConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    user_id: UUID
    title: str
    provider: str
    model: str | None = None
    temperature: float
    max_tokens: int
    citation_mode: str
    streaming_on: bool
    created_at: datetime
    updated_at: datetime
    messages: List[AIMessageResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AIModelInfo(BaseModel):
    provider: str
    model_id: str
    name: str
    max_tokens: int

