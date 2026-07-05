import abc
from datetime import UTC, datetime, timedelta
from uuid import UUID
from app.models.knowledge import KnowledgeItem


class FusionStrategy(abc.ABC):
    @abc.abstractmethod
    def fuse(
        self,
        lexical_results: list[tuple[KnowledgeItem, float]],
        semantic_results: list[tuple[KnowledgeItem, float]],
        **kwargs
    ) -> list[tuple[KnowledgeItem, dict]]:
        """
        Combine lexical and semantic results.
        Returns:
            list of (KnowledgeItem, score_explanation_dict)
        """
        pass


class ReciprocalRankFusion(FusionStrategy):
    def __init__(self, k: int = 60) -> None:
        self.k = k

    def fuse(
        self,
        lexical_results: list[tuple[KnowledgeItem, float]],
        semantic_results: list[tuple[KnowledgeItem, float]],
        **kwargs
    ) -> list[tuple[KnowledgeItem, dict]]:
        # Map item ID -> (item, rank_in_lexical)
        lexical_ranks = {item.id: (item, idx + 1, score) for idx, (item, score) in enumerate(lexical_results)}
        # Map item ID -> (item, rank_in_semantic)
        semantic_ranks = {item.id: (item, idx + 1, score) for idx, (item, score) in enumerate(semantic_results)}

        all_item_ids = set(lexical_ranks.keys()) | set(semantic_ranks.keys())
        fused = []

        for item_id in all_item_ids:
            item = None
            rrf_score = 0.0
            lexical_rank = None
            semantic_rank = None
            lexical_score = 0.0
            semantic_score = 0.0

            if item_id in lexical_ranks:
                item, rank, score = lexical_ranks[item_id]
                rrf_score += 1.0 / (self.k + rank)
                lexical_rank = rank
                lexical_score = score

            if item_id in semantic_ranks:
                item, rank, score = semantic_ranks[item_id]
                rrf_score += 1.0 / (self.k + rank)
                semantic_rank = rank
                semantic_score = score

            fused.append((
                item,
                {
                    "rrf_score": rrf_score,
                    "lexical_rank": lexical_rank,
                    "semantic_rank": semantic_rank,
                    "lexical_score": lexical_score,
                    "semantic_score": semantic_score,
                }
            ))

        # Sort by RRF score descending
        fused.sort(key=lambda x: x[1]["rrf_score"], reverse=True)
        return fused


class WeightedReRanker:
    """
    Re-ranks search results based on multiple configurable signals:
    - RRF score or Lexical/Semantic raw scores
    - Source reliability bonus
    - Document freshness/recency bonus
    """
    def __init__(
        self,
        weights: dict | None = None
    ) -> None:
        # Default weights
        self.weights = weights or {
            "rrf": 0.4,
            "semantic": 0.3,
            "recency": 0.15,
            "source": 0.15
        }

    def re_rank(
        self,
        fused_results: list[tuple[KnowledgeItem, dict]],
        **kwargs
    ) -> list[tuple[KnowledgeItem, float, dict]]:
        """
        Applies weighted scoring to fused results.
        Returns:
            list of (KnowledgeItem, final_score, score_explanation)
        """
        re_ranked = []
        now = datetime.now(UTC)

        for item, info in fused_results:
            # 1. RRF score component (normalized to roughly 0-1)
            # RRF score max possible is 2 * (1 / (60 + 1)) = ~0.032. Let's normalize it to 0-1 by dividing by 0.033
            norm_rrf = min(info["rrf_score"] / 0.033, 1.0)

            # 2. Semantic score component (already cosine similarity, typically 0-1)
            semantic_score = info["semantic_score"]

            # 3. Recency score component (0 to 1 based on age, exponential decay or linear over 30 days)
            age_days = (now - item.updated_time.replace(tzinfo=UTC)).days
            age_days = max(0, age_days)
            recency_score = max(0.0, 1.0 - (age_days / 30.0))  # 1.0 at day 0, 0.0 at day 30+

            # 4. Source score component (Notion=1.0, GitHub=0.8, Drive=0.6, others=0.4)
            source_score = 0.4
            if item.source == "notion":
                source_score = 1.0
            elif item.source == "github":
                source_score = 0.8
            elif item.source == "google_drive":
                source_score = 0.6

            # Compute final weighted score
            final_score = (
                self.weights.get("rrf", 0.4) * norm_rrf +
                self.weights.get("semantic", 0.3) * semantic_score +
                self.weights.get("recency", 0.15) * recency_score +
                self.weights.get("source", 0.15) * source_score
            )

            # Build explainability reasons
            reasons = []
            matching_fields = []
            
            if info["lexical_rank"]:
                reasons.append(f"Keyword match (Lexical Rank: {info['lexical_rank']})")
                matching_fields.append("title")
                if item.content and len(item.content) > 0:
                    matching_fields.append("content")
            if info["semantic_rank"]:
                reasons.append(f"Semantic similarity match ({info['semantic_score']:.2f} score)")
                matching_fields.append("embedding")
            if age_days <= 7:
                reasons.append("Recently updated (within 7 days)")
            elif age_days <= 30:
                reasons.append("Fresh document (within 30 days)")

            explanation = {
                "lexical_score": info["lexical_score"],
                "semantic_score": info["semantic_score"],
                "rrf_score": info["rrf_score"],
                "recency_score": recency_score,
                "source_score": source_score,
                "matching_fields": list(set(matching_fields)),
                "reasons": reasons
            }

            re_ranked.append((item, final_score, explanation))

        # Sort by final score descending
        re_ranked.sort(key=lambda x: x[1], reverse=True)
        return re_ranked
