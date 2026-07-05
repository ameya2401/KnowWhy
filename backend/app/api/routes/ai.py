from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.knowledge import require_project_membership
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.config import settings
from app.schemas.ai import (
    AIQueryRequest,
    AIExplainRequest,
    AIQueryResponse,
    AIProvidersResponse,
    AIStatisticsResponse,
    LLMProviderInfo,
    AIChatRequest,
    AIConversationResponse,
    AIModelInfo,
)
from app.services.ai import AIIntelligenceService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/query", response_model=AIQueryResponse)
async def query_intelligence_engine(
    request: AIQueryRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Executes the complete RAG pipeline on a user query with project membership protection."""
    await require_project_membership(current_user, request.project_id, db)
    service = AIIntelligenceService(db)
    return await service.execute_rag(
        project_id=request.project_id,
        user_id=current_user.id,
        query=request.q,
        provider_override=request.provider,
        is_explain=False,
    )


@router.post("/explain", response_model=AIQueryResponse)
async def explain_concept(
    request: AIExplainRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Executes the explanation extraction RAG sub-pipeline."""
    await require_project_membership(current_user, request.project_id, db)
    service = AIIntelligenceService(db)
    query = f"Explain the concept of '{request.concept}' and detail its components, dependencies, and implementation context."
    return await service.execute_rag(
        project_id=request.project_id,
        user_id=current_user.id,
        query=query,
        provider_override=request.provider,
        is_explain=True,
    )


@router.get("/providers", response_model=AIProvidersResponse)
async def list_providers(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Returns lists of supported, active, and available (API keys set) LLM providers."""
    providers = [
        LLMProviderInfo(
            id="openai",
            name="OpenAI GPT Models",
            is_active=settings.llm_provider == "openai",
            is_available=bool(settings.openai_api_key),
        ),
        LLMProviderInfo(
            id="anthropic",
            name="Anthropic Claude",
            is_active=settings.llm_provider == "anthropic",
            is_available=bool(settings.anthropic_api_key),
        ),
        LLMProviderInfo(
            id="gemini",
            name="Google Gemini",
            is_active=settings.llm_provider == "gemini",
            is_available=bool(settings.gemini_api_key),
        ),
    ]
    return AIProvidersResponse(
        providers=providers,
        active_provider=settings.llm_provider,
    )


@router.get("/statistics", response_model=AIStatisticsResponse)
async def get_ai_statistics(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Yields telemetry on AI query processing speed, tokens consumed, and quality metrics."""
    diag = AIIntelligenceService.get_diagnostics()
    return AIStatisticsResponse(
        total_requests=diag["total_requests"],
        average_latency_ms=diag["average_latency_ms"],
        total_tokens_used=diag["total_tokens_used"],
        average_confidence=diag["average_confidence"],
    )


@router.post("/chat")
async def chat_with_assistant(
    request: AIChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Conversational chat assistant that responds with streaming or standard response."""
    await require_project_membership(current_user, request.project_id, db)
    service = AIIntelligenceService(db)
    result = await service.execute_chat(request, current_user.id)
    if result.get("streaming"):
        return StreamingResponse(
            result["generator"](),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    return result


@router.get("/conversations", response_model=List[AIConversationResponse])
async def get_conversations(
    project_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
    q: str | None = None,
):
    """Retrieves saved conversations for a project context with optional keyword searching."""
    await require_project_membership(current_user, project_id, db)
    service = AIIntelligenceService(db)
    convs = await service.list_conversations(project_id, current_user.id, q)
    return [AIConversationResponse.model_validate(c) for c in convs]


@router.get("/conversations/{id}", response_model=AIConversationResponse)
async def get_conversation_by_id(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Retrieves conversation thread by id with complete chronological messages."""
    service = AIIntelligenceService(db)
    conv = await service.get_conversation(id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_project_membership(current_user, conv.project_id, db)
    return AIConversationResponse.model_validate(conv)


@router.delete("/conversations/{id}")
async def delete_conversation_by_id(
    id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_database_session)],
):
    """Deletes conversation thread history."""
    service = AIIntelligenceService(db)
    conv = await service.get_conversation(id, current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_project_membership(current_user, conv.project_id, db)
    success = await service.delete_conversation(id, current_user.id)
    return {"success": success}


@router.get("/models", response_model=List[AIModelInfo])
async def list_models(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lists supported model versions and token configurations for settings customization."""
    return [
        AIModelInfo(provider="openai", model_id="gpt-4o-mini", name="GPT-4o Mini", max_tokens=128000),
        AIModelInfo(provider="openai", model_id="gpt-4o", name="GPT-4o", max_tokens=128000),
        AIModelInfo(provider="anthropic", model_id="claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet", max_tokens=200000),
        AIModelInfo(provider="anthropic", model_id="claude-3-5-haiku-20241022", name="Claude 3.5 Haiku", max_tokens=200000),
        AIModelInfo(provider="gemini", model_id="gemini-1.5-flash", name="Gemini 1.5 Flash", max_tokens=1000000),
        AIModelInfo(provider="gemini", model_id="gemini-1.5-pro", name="Gemini 1.5 Pro", max_tokens=2000000),
        AIModelInfo(provider="mock", model_id="mock", name="Simulated Mock Model", max_tokens=4000),
    ]
