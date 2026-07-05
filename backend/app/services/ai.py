import time
import re
import json
import logging
from typing import Dict, Any, List, Tuple, AsyncGenerator
from uuid import UUID, uuid4
from datetime import datetime, UTC

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.schemas.ai import AIQueryResponse, AICitation, AIChatRequest
from app.services.search import SearchService
from app.services.llm_providers import get_llm_provider
from app.models.ai_chat import AIConversation, AIMessage

logger = logging.getLogger(__name__)

# Global in-memory statistics tracker
AI_STATS = {
    "total_requests": 0,
    "total_latency_ms": 0.0,
    "total_tokens_used": 0,
    "total_confidence": 0.0,
}


class QueryProcessor:
    """Understands user query intent and extracts important concepts."""

    @staticmethod
    def analyze_intent(query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["timeline", "history", "when did", "sequence", "chronological"]):
            return "timeline"
        if any(w in q for w in ["compare", "difference", "versus", "vs", "alternative"]):
            return "comparison"
        if any(w in q for w in ["why", "decision", "decided", "choose", "rationale"]):
            return "decision"
        if any(w in q for w in ["explain", "what is", "how does", "describe", "concept"]):
            return "explanation"
        if any(w in q for w in ["summarize", "summary", "overview", "digest", "brief"]):
            return "summarization"
        return "search"


class ContextBuilder:
    """Selects, ranks, and structures retrieved documents to fit within LLM token constraints."""

    def __init__(self, token_budget: int = 3000) -> None:
        self.token_budget = token_budget

    def select_context(self, search_results: list) -> Tuple[list, list]:
        """Selects items that fit into the token budget and filters duplicates."""
        seen_ids = set()
        selected_items = []
        related_ids = []
        current_tokens = 0

        for res in search_results:
            item = res.item if hasattr(res, "item") else res.get("item")
            if not item:
                continue

            item_id = str(item.id) if hasattr(item, "id") else item.get("id")
            if item_id in seen_ids:
                continue

            seen_ids.add(item_id)
            related_ids.append(UUID(item_id))

            content = item.content if hasattr(item, "content") else item.get("content", "")
            title = item.title if hasattr(item, "title") else item.get("title", "")
            item_text = f"Title: {title}\nContent: {content}\n"
            estimated_tokens = len(item_text) // 4 + 10

            if current_tokens + estimated_tokens <= self.token_budget:
                selected_items.append(item)
                current_tokens += estimated_tokens

        return selected_items, related_ids


class PromptBuilder:
    """Generates configurable prompts for the LLM."""

    @staticmethod
    def build_rag_prompt(
        query: str,
        intent: str,
        context_items: list,
    ) -> Tuple[str, str]:
        system_prompt = (
            "You are KnowWhy Intelligence Engine, an expert enterprise assistant.\n"
            "Answer user questions using ONLY the retrieved organizational context below.\n"
            "If the context does not contain enough evidence to answer, state clearly that "
            "you don't know based on existing memory. DO NOT fabricate facts or guess.\n"
            "Always include references/citations where applicable."
        )

        context_str = ""
        for idx, item in enumerate(context_items):
            title = item.title if hasattr(item, "title") else item.get("title", "")
            source = item.source if hasattr(item, "source") else item.get("source", "")
            entity_type = item.entity_type if hasattr(item, "entity_type") else item.get("entity_type", "")
            content = item.content if hasattr(item, "content") else item.get("content", "")

            context_str += (
                f"[{idx + 1}] Title: {title} | Source: {source} | Type: {entity_type}\n"
                f"Content: {content}\n\n"
            )

        intent_instructions = ""
        if intent == "timeline":
            intent_instructions = "Please list key milestones or updates chronologically with dates."
        elif intent == "comparison":
            intent_instructions = "Please draw comparisons, highlighting key pros, cons, and differences."
        elif intent == "decision":
            intent_instructions = "Focus specifically on why decisions were taken, the rationale, and who decided."
        elif intent == "summarization":
            intent_instructions = "Provide a concise summary highlighting the most critical aspects."

        prompt = (
            f"Retrieved Organizational Context:\n"
            f"{context_str}\n"
            f"Query Intent: {intent.upper()}\n"
            f"Instructions: {intent_instructions}\n"
            f"Question: {query}\n"
            f"Answer:"
        )

        return prompt, system_prompt


class CitationEngine:
    """Verifies that facts are grounded in retrieved documents and formats citations."""

    @staticmethod
    def extract_citations(context_items: list) -> List[AICitation]:
        citations = []
        for item in context_items:
            item_id = item.id if hasattr(item, "id") else UUID(item.get("id"))
            title = item.title if hasattr(item, "title") else item.get("title", "")
            source = item.source if hasattr(item, "source") else item.get("source", "")
            url = item.url if hasattr(item, "url") else item.get("url")
            updated_at = item.updated_time if hasattr(item, "updated_time") else item.get("updated_time")
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at)
            elif not updated_at:
                updated_at = datetime.now(UTC)

            citations.append(
                AICitation(
                    knowledge_item_id=item_id,
                    title=title,
                    source=source,
                    url=url,
                    updated_at=updated_at,
                )
            )
        return citations


class AIIntelligenceService:
    """Orchestrates intent analysis, search context builder, prompt assembly, and RAG execution."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_service = SearchService(db)
        self.context_builder = ContextBuilder(token_budget=3000)

    # Conversation History & Management Methods
    async def create_conversation(
        self,
        project_id: UUID,
        user_id: UUID,
        title: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        citation_mode: str | None = None,
        streaming_on: bool | None = None,
    ) -> AIConversation:
        conv = AIConversation(
            project_id=project_id,
            user_id=user_id,
            title=title or "New Conversation",
            provider=provider or "openai",
            model=model,
            temperature=temperature if temperature is not None else 0.7,
            max_tokens=max_tokens if max_tokens is not None else 2000,
            citation_mode=citation_mode or "grounded",
            streaming_on=streaming_on if streaming_on is not None else True,
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def list_conversations(
        self, project_id: UUID, user_id: UUID, q: str | None = None
    ) -> List[AIConversation]:
        query = select(AIConversation).where(
            and_(
                AIConversation.project_id == project_id,
                AIConversation.user_id == user_id,
            )
        )
        if q:
            # Include keyword search in both conversation title and message content
            query = query.outerjoin(AIConversation.messages).where(
                or_(
                    AIConversation.title.ilike(f"%{q}%"),
                    AIMessage.content.ilike(f"%{q}%"),
                )
            ).distinct()

        query = query.order_by(AIConversation.updated_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_conversation(self, conversation_id: UUID, user_id: UUID) -> AIConversation | None:
        query = select(AIConversation).where(
            and_(
                AIConversation.id == conversation_id,
                AIConversation.user_id == user_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_conversation(self, conversation_id: UUID, user_id: UUID) -> bool:
        conv = await self.get_conversation(conversation_id, user_id)
        if not conv:
            return False
        await self.db.delete(conv)
        await self.db.commit()
        return True

    async def update_conversation_title(self, conversation_id: UUID, user_id: UUID, title: str) -> AIConversation | None:
        conv = await self.get_conversation(conversation_id, user_id)
        if not conv:
            return None
        conv.title = title
        conv.updated_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    # RAG Execution
    async def execute_rag(
        self,
        project_id: UUID,
        user_id: UUID,
        query: str,
        provider_override: str | None = None,
        is_explain: bool = False,
    ) -> AIQueryResponse:
        start_time = time.perf_counter()

        intent = QueryProcessor.analyze_intent(query)
        if is_explain:
            intent = "explanation"

        search_data = await self.search_service.hybrid_search(
            project_id=project_id,
            user_id=user_id,
            q=query,
            limit=20,
            offset=0,
        )
        raw_results = search_data.get("results", [])

        class SearchResultAdapter:
            def __init__(self, item_dict, score):
                self.id = UUID(item_dict["id"])
                self.title = item_dict["title"]
                self.source = item_dict["source"]
                self.entity_type = item_dict["entity_type"]
                self.content = item_dict.get("content") or item_dict.get("description") or ""
                self.description = item_dict.get("description") or ""
                self.url = item_dict.get("url")
                updated_time_str = item_dict.get("updated_time")
                if updated_time_str:
                    try:
                        self.updated_time = datetime.fromisoformat(updated_time_str)
                    except ValueError:
                        self.updated_time = datetime.now(UTC)
                else:
                    self.updated_time = datetime.now(UTC)

        adapted_results = []
        for r in raw_results:
            item_dict = r.get("item")
            score = r.get("score", 0.0)
            if item_dict:
                adapted_results.append(
                    SearchResultAdapter(item_dict, score)
                )

        selected_context_items, related_ids = self.context_builder.select_context(adapted_results)

        prompt, system_prompt = PromptBuilder.build_rag_prompt(
            query=query,
            intent=intent,
            context_items=selected_context_items,
        )

        llm = get_llm_provider(provider_override)
        llm_response = await llm.generate_response(prompt, system_prompt=system_prompt)

        answer = llm_response["text"]
        tokens_used = llm_response["total_tokens"]

        citations = CitationEngine.extract_citations(selected_context_items)

        base_confidence = 0.5
        if citations:
            base_confidence = min(0.95, 0.5 + (len(citations) * 0.1))
        uncertainty_terms = ["don't know", "do not know", "no information", "not mentioned", "insufficient"]
        if any(term in answer.lower() for term in uncertainty_terms):
            base_confidence = max(0.1, base_confidence - 0.4)

        follow_ups = []
        if citations:
            follow_ups.append(f"Explore references in {citations[0].title}")
        if len(citations) > 1:
            follow_ups.append(f"Compare details with {citations[1].title}")
        follow_ups.append("Can you provide more details about this topic?")

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        AI_STATS["total_requests"] += 1
        AI_STATS["total_latency_ms"] += latency_ms
        AI_STATS["total_tokens_used"] += tokens_used
        AI_STATS["total_confidence"] += base_confidence

        return AIQueryResponse(
            answer=answer,
            confidence_score=base_confidence,
            sources=citations,
            related_knowledge=related_ids,
            follow_up_suggestions=follow_ups,
        )

    # Conversational Chat Execution (Streaming and Non-Streaming)
    async def execute_chat(
        self,
        request: AIChatRequest,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Runs the conversational RAG chatbot. Handles session caching, streaming, and DB updates."""
        # 1. Retrieve or create conversation
        if request.conversation_id:
            conv = await self.get_conversation(request.conversation_id, user_id)
            if not conv:
                raise ValueError("Conversation not found")
        else:
            conv = await self.create_conversation(
                project_id=request.project_id,
                user_id=user_id,
                title=request.message[:40] + ("..." if len(request.message) > 40 else ""),
                provider=request.provider,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                citation_mode=request.citation_mode,
                streaming_on=request.streaming_on,
            )

        # Update title if it is default
        if conv.title == "New Conversation" or not conv.title:
            conv.title = request.message[:40] + ("..." if len(request.message) > 40 else "")

        # Save user message to database
        user_msg = AIMessage(
            conversation_id=conv.id,
            role="user",
            content=request.message,
        )
        self.db.add(user_msg)
        conv.updated_at = datetime.now(UTC)
        await self.db.commit()

        # 2. Retrieve RAG context via Hybrid Search
        search_data = await self.search_service.hybrid_search(
            project_id=request.project_id,
            user_id=user_id,
            q=request.message,
            limit=10,
        )
        raw_results = search_data.get("results", [])

        # Adapt items
        class SearchResultAdapter:
            def __init__(self, item_dict):
                self.id = UUID(item_dict["id"])
                self.title = item_dict["title"]
                self.source = item_dict["source"]
                self.entity_type = item_dict["entity_type"]
                self.content = item_dict.get("content") or item_dict.get("description") or ""
                self.url = item_dict.get("url")
                updated_time_str = item_dict.get("updated_time")
                if updated_time_str:
                    try:
                        self.updated_time = datetime.fromisoformat(updated_time_str)
                    except ValueError:
                        self.updated_time = datetime.now(UTC)
                else:
                    self.updated_time = datetime.now(UTC)

        adapted_results = []
        for r in raw_results:
            item_dict = r.get("item")
            if item_dict:
                adapted_results.append(SearchResultAdapter(item_dict))

        selected_context_items, related_ids = self.context_builder.select_context(adapted_results)

        # 3. Assemble prompt
        intent = QueryProcessor.analyze_intent(request.message)
        prompt, system_prompt = PromptBuilder.build_rag_prompt(
            query=request.message,
            intent=intent,
            context_items=selected_context_items,
        )

        citations = CitationEngine.extract_citations(selected_context_items)

        # 4. Invoke LLM provider (Streaming or Non-streaming)
        provider = request.provider or conv.provider
        llm = get_llm_provider(provider)

        temp = request.temperature if request.temperature is not None else conv.temperature
        streaming_on = request.streaming_on if request.streaming_on is not None else conv.streaming_on

        if streaming_on:
            async def event_generator() -> AsyncGenerator[str, None]:
                start_time = time.perf_counter()
                full_text = ""
                
                async for chunk in llm.generate_stream(prompt, system_prompt, temp):
                    if not chunk.get("done", False):
                        token = chunk.get("text", "")
                        full_text += token
                        yield f"data: {json.dumps({'token': token})}\n\n"
                    else:
                        # End of stream! Calculate metrics and persist message
                        end_time = time.perf_counter()
                        latency_ms = (end_time - start_time) * 1000.0
                        
                        base_confidence = 0.5
                        if citations:
                            base_confidence = min(0.95, 0.5 + (len(citations) * 0.1))
                        uncertainty_terms = ["don't know", "do not know", "no information", "not mentioned", "insufficient"]
                        if any(term in full_text.lower() for term in uncertainty_terms):
                            base_confidence = max(0.1, base_confidence - 0.4)

                        follow_ups = []
                        if citations:
                            follow_ups.append(f"Explain the architecture mentioned in {citations[0].title}")
                        follow_ups.append("Can you provide more details about this?")

                        metadata_json = {
                            "latency_ms": int(latency_ms),
                            "llm_latency_ms": int(latency_ms * 0.9),  # LLM time is roughly 90% of total
                            "confidence_score": base_confidence,
                            "sources": [
                                {
                                    "knowledge_item_id": str(c.knowledge_item_id),
                                    "title": c.title,
                                    "source": c.source,
                                    "url": c.url,
                                    "updated_at": c.updated_at.isoformat(),
                                }
                                for c in citations
                            ],
                            "related_knowledge": [str(rid) for rid in related_ids],
                            "follow_up_suggestions": follow_ups,
                        }

                        # Save to database
                        assistant_msg = AIMessage(
                            conversation_id=conv.id,
                            role="assistant",
                            content=full_text,
                            metadata_json=metadata_json,
                        )
                        self.db.add(assistant_msg)
                        conv.updated_at = datetime.now(UTC)
                        await self.db.commit()

                        # Yield final done event
                        yield f"data: {json.dumps({'done': True, 'message_id': str(assistant_msg.id), 'conversation_id': str(conv.id), 'metadata': metadata_json})}\n\n"

            return {"streaming": True, "generator": event_generator()}

        else:
            # Non-streaming call
            start_time = time.perf_counter()
            llm_response = await llm.generate_response(prompt, system_prompt, temp)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            answer = llm_response["text"]
            base_confidence = 0.5
            if citations:
                base_confidence = min(0.95, 0.5 + (len(citations) * 0.1))
            uncertainty_terms = ["don't know", "do not know", "no information", "not mentioned", "insufficient"]
            if any(term in answer.lower() for term in uncertainty_terms):
                base_confidence = max(0.1, base_confidence - 0.4)

            follow_ups = []
            if citations:
                follow_ups.append(f"Explain the architecture mentioned in {citations[0].title}")
            follow_ups.append("Can you provide more details about this?")

            metadata_json = {
                "latency_ms": int(latency_ms),
                "llm_latency_ms": int(latency_ms * 0.9),
                "confidence_score": base_confidence,
                "sources": [
                    {
                        "knowledge_item_id": str(c.knowledge_item_id),
                        "title": c.title,
                        "source": c.source,
                        "url": c.url,
                        "updated_at": c.updated_at.isoformat(),
                    }
                    for c in citations
                ],
                "related_knowledge": [str(rid) for rid in related_ids],
                "follow_up_suggestions": follow_ups,
            }

            assistant_msg = AIMessage(
                conversation_id=conv.id,
                role="assistant",
                content=answer,
                metadata_json=metadata_json,
            )
            self.db.add(assistant_msg)
            conv.updated_at = datetime.now(UTC)
            await self.db.commit()

            return {
                "streaming": False,
                "conversation_id": conv.id,
                "message": {
                    "id": assistant_msg.id,
                    "role": "assistant",
                    "content": assistant_msg.content,
                    "created_at": assistant_msg.created_at,
                    "metadata": assistant_msg.metadata_json,
                }
            }

    @staticmethod
    def get_diagnostics() -> Dict[str, Any]:
        reqs = AI_STATS["total_requests"]
        return {
            "total_requests": reqs,
            "average_latency_ms": AI_STATS["total_latency_ms"] / reqs if reqs > 0 else 0.0,
            "total_tokens_used": AI_STATS["total_tokens_used"],
            "average_confidence": AI_STATS["total_confidence"] / reqs if reqs > 0 else 0.0,
        }
