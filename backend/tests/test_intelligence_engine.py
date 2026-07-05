from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import app.api.routes.ai as ai_router
from app.database.session import get_database_session
from app.dependencies.auth import get_current_user
from app.main import create_app
from app.models.user import AuthProvider, User
from app.services.ai import (
    AIIntelligenceService,
    CitationEngine,
    ContextBuilder,
    PromptBuilder,
    QueryProcessor,
)
from app.services.llm_providers import MockLLMProvider, OpenAIProvider, get_llm_provider


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app()

    async def override_db():
        yield None

    user = User(
        id=uuid4(),
        email="engineer@example.com",
        full_name="KnowWhy Engineer",
        profile_picture_url=None,
        provider=AuthProvider.GITHUB,
        provider_id="123",
        is_active=True,
        last_login_at=datetime.now(UTC),
    )

    async def override_current_user() -> User:
        return user

    app.dependency_overrides[get_database_session] = override_db
    app.dependency_overrides[get_current_user] = override_current_user

    async def mock_require_membership(*args, **kwargs):
        return None

    monkeypatch.setattr(ai_router, "require_project_membership", mock_require_membership)

    return TestClient(app)


def test_query_intent_analysis():
    """Verify that user query intent is detected correctly based on keyword rules."""
    assert QueryProcessor.analyze_intent("Give me the chronological history of updates") == "timeline"  # noqa: E501
    assert QueryProcessor.analyze_intent("What is the difference between Redis and Memcached?") == "comparison"  # noqa: E501
    assert QueryProcessor.analyze_intent("Why did we adopt auth0 instead of self-hosted OAuth?") == "decision"  # noqa: E501
    assert QueryProcessor.analyze_intent("What is authentication?") == "explanation"
    assert QueryProcessor.analyze_intent("Can you summarize the meeting details?") == "summarization"  # noqa: E501
    assert QueryProcessor.analyze_intent("List all project files") == "search"


def test_context_builder_token_budget():
    """Verify that ContextBuilder respects token budgets and removes duplicate documents."""
    builder = ContextBuilder(token_budget=100)

    class MockItem:
        def __init__(self, item_id, title, content):
            self.id = item_id
            self.title = title
            self.content = content
            self.source = "mock"
            self.entity_type = "document"

    item1 = MockItem(uuid4(), "Title A", "Very long content " * 10)  # ~50-60 tokens
    item2 = MockItem(uuid4(), "Title B", "Short content")  # ~15-20 tokens
    item3 = MockItem(item2.id, "Title B Duplicate", "Short content")  # Duplicate ID
    item4 = MockItem(uuid4(), "Title C", "Some extra content " * 10)  # ~50-60 tokens

    results = [
        {"item": item1},
        {"item": item2},
        {"item": item3},
        {"item": item4},
    ]

    selected, related = builder.select_context(results)
    assert len(selected) == 2
    assert selected[0].id == item1.id
    assert selected[1].id == item2.id
    assert len(related) == 3  # Related retains all unique item IDs (item1, item2, item4)


def test_prompt_builder():
    """Verify PromptBuilder constructs valid templates containing instructions, query, and context."""  # noqa: E501
    class DummyItem:
        title = "Doc A"
        source = "github"
        entity_type = "file"
        content = "Line content for doc A."

    prompt, system = PromptBuilder.build_rag_prompt(
        query="Explain Doc A?",
        intent="explanation",
        context_items=[DummyItem()],
    )

    assert "You are KnowWhy Intelligence Engine" in system
    assert "Doc A" in prompt
    assert "github" in prompt
    assert "Line content for doc A." in prompt
    assert "Explain Doc A?" in prompt


def test_citation_engine():
    """Verify that CitationEngine builds structured citation metrics."""
    item_id = uuid4()
    class DummyItem:
        id = item_id
        title = "Doc A"
        source = "github"
        url = "https://github.com/org/repo"
        updated_time = datetime(2026, 7, 5, 12, 0, 0, tzinfo=UTC)

    citations = CitationEngine.extract_citations([DummyItem()])
    assert len(citations) == 1
    assert citations[0].knowledge_item_id == item_id
    assert citations[0].title == "Doc A"
    assert citations[0].source == "github"
    assert citations[0].url == "https://github.com/org/repo"
    assert citations[0].updated_at == datetime(2026, 7, 5, 12, 0, 0, tzinfo=UTC)


def test_provider_switching():
    """Verify that LLM providers are interchangeable and resolve correctly."""
    p_mock = get_llm_provider("mock")
    assert isinstance(p_mock, MockLLMProvider)

    p_openai = get_llm_provider("openai")
    assert isinstance(p_openai, OpenAIProvider) or isinstance(p_openai, MockLLMProvider)


@pytest.mark.asyncio
async def test_mock_llm_generation():
    """Verify MockLLMProvider synthesizes prompt and respects schema return shapes."""
    provider = MockLLMProvider()
    res = await provider.generate_response(
        prompt="Context:\nTitle: Mock Document\nQuestion: Summarize context",
        system_prompt="System Prompt",
    )
    assert "text" in res
    assert "Mock Document" in res["text"]
    assert res["total_tokens"] > 0


def test_ai_query_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify project members can access RAG query route and receive valid citations."""
    async def mock_execute_rag(self, project_id, user_id, query, provider_override=None, is_explain=False):  # noqa: E501
        from app.schemas.ai import AICitation, AIQueryResponse
        return AIQueryResponse(
            answer="This is a test RAG response.",
            confidence_score=0.9,
            sources=[
                AICitation(
                    knowledge_item_id=uuid4(),
                    title="Mock doc",
                    source="github",
                    url=None,
                    updated_at=datetime.now(UTC),
                )
            ],
            related_knowledge=[],
            follow_up_suggestions=["Follow up details?"],
        )

    monkeypatch.setattr(AIIntelligenceService, "execute_rag", mock_execute_rag)

    payload = {
        "project_id": str(uuid4()),
        "q": "What is the timeline of the auth project?",
        "provider": "mock",
    }
    response = client.post("/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a test RAG response."
    assert data["confidence_score"] == 0.9
    assert len(data["sources"]) == 1


def test_ai_explain_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify RAG explanation endpoint returns structured output."""
    async def mock_execute_rag(self, project_id, user_id, query, provider_override=None, is_explain=False):  # noqa: E501
        from app.schemas.ai import AIQueryResponse
        return AIQueryResponse(
            answer="OAuth2 details here.",
            confidence_score=0.85,
            sources=[],
            related_knowledge=[],
            follow_up_suggestions=["More oauth?"],
        )

    monkeypatch.setattr(AIIntelligenceService, "execute_rag", mock_execute_rag)

    payload = {
        "project_id": str(uuid4()),
        "concept": "OAuth2 Authentication Flow",
        "provider": "mock",
    }
    response = client.post("/ai/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "OAuth2 details here."
    assert len(data["follow_up_suggestions"]) == 1


def test_ai_diagnostics_and_providers_endpoints(client: TestClient):
    """Verify list of providers and diagnostic statistics return correct structures."""
    # List providers
    prov_res = client.get("/ai/providers")
    assert prov_res.status_code == 200
    p_data = prov_res.json()
    assert "providers" in p_data
    assert "active_provider" in p_data
    assert len(p_data["providers"]) == 3

    # List statistics
    stats_res = client.get("/ai/statistics")
    assert stats_res.status_code == 200
    s_data = stats_res.json()
    assert "total_requests" in s_data
    assert "average_latency_ms" in s_data


def test_ai_models_endpoint(client: TestClient):
    """Verify listing supported models works."""
    res = client.get("/ai/models")
    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    assert data[0]["provider"] == "openai"
    assert "model_id" in data[0]


def test_chat_conversations_api(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify creating, listing, getting, and deleting conversations via API."""
    project_id = uuid4()
    
    # Mock services in AIIntelligenceService
    conversations_db = []
    
    class DummyConversation:
        def __init__(self, **kwargs):
            self.id = uuid4()
            self.project_id = project_id
            self.user_id = uuid4()
            self.title = kwargs.get("title", "New Conversation")
            self.provider = "mock"
            self.model = "mock"
            self.temperature = 0.7
            self.max_tokens = 2000
            self.citation_mode = "grounded"
            self.streaming_on = False
            self.created_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)
            self.messages = []
            
    async def mock_create_conversation(self, **kwargs):
        c = DummyConversation(**kwargs)
        conversations_db.append(c)
        return c

    async def mock_list_conversations(self, project_id, user_id, q=None):
        return conversations_db

    async def mock_get_conversation(self, conversation_id, user_id):
        for c in conversations_db:
            if c.id == conversation_id:
                return c
        return None

    async def mock_delete_conversation(self, conversation_id, user_id):
        for c in conversations_db:
            if c.id == conversation_id:
                conversations_db.remove(c)
                return True
        return False

    monkeypatch.setattr(AIIntelligenceService, "create_conversation", mock_create_conversation)
    monkeypatch.setattr(AIIntelligenceService, "list_conversations", mock_list_conversations)
    monkeypatch.setattr(AIIntelligenceService, "get_conversation", mock_get_conversation)
    monkeypatch.setattr(AIIntelligenceService, "delete_conversation", mock_delete_conversation)

    # List conversations (should be empty initially)
    res = client.get(f"/ai/conversations?project_id={project_id}")
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Add a mock conversation
    c = DummyConversation(title="Testing conversation")
    conversations_db.append(c)

    res = client.get(f"/ai/conversations?project_id={project_id}")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["title"] == "Testing conversation"

    # Get single conversation
    c_id = str(c.id)
    res = client.get(f"/ai/conversations/{c_id}")
    assert res.status_code == 200
    assert res.json()["id"] == c_id

    # Delete conversation
    res = client.delete(f"/ai/conversations/{c_id}")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # List should be empty again
    res = client.get(f"/ai/conversations?project_id={project_id}")
    assert len(res.json()) == 0


def test_chat_non_streaming_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify chat non-streaming RAG response."""
    project_id = uuid4()
    
    async def mock_execute_chat(self, request, user_id):
        return {
            "streaming": False,
            "conversation_id": uuid4(),
            "message": {
                "id": uuid4(),
                "role": "assistant",
                "content": "This is a non-streaming mock RAG response.",
                "created_at": datetime.now(UTC),
                "metadata": {
                    "confidence_score": 0.95,
                    "sources": [],
                }
            }
        }
        
    monkeypatch.setattr(AIIntelligenceService, "execute_chat", mock_execute_chat)

    payload = {
        "project_id": str(project_id),
        "message": "Hello AI",
        "streaming_on": False,
    }
    res = client.post("/ai/chat", json=payload)
    assert res.status_code == 200
    assert "message" in res.json()
    assert res.json()["message"]["content"] == "This is a non-streaming mock RAG response."


def test_chat_streaming_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    """Verify chat streaming endpoint yields SSE stream."""
    project_id = uuid4()

    async def mock_execute_chat(self, request, user_id):
        async def mock_gen():
            yield "data: {\"token\": \"Hello\"}\n\n"
            yield "data: {\"token\": \" world\"}\n\n"
            yield "data: {\"done\": true, \"metadata\": {}}\n\n"
            
        return {
            "streaming": True,
            "generator": mock_gen,
        }

    monkeypatch.setattr(AIIntelligenceService, "execute_chat", mock_execute_chat)

    payload = {
        "project_id": str(project_id),
        "message": "Stream hello",
        "streaming_on": True,
    }
    res = client.post("/ai/chat", json=payload)
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    
    # Read stream chunks
    lines = [line if isinstance(line, str) else line.decode("utf-8") for line in res.iter_lines() if line]  # noqa: E501
    assert len(lines) == 3
    assert "Hello" in lines[0]
    assert "world" in lines[1]
    assert "done" in lines[2]

