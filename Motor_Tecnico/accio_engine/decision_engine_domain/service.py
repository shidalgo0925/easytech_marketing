from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.ports import KnowledgeReader
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.priority_scorer import PriorityScorer
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.rules import evaluate_all_rules


class RoadmapBuilderService:
    """M10.1–M10.2 — rules + priority scoring."""

    def __init__(
        self,
        knowledge_reader: KnowledgeReader,
        priority_scorer: PriorityScorer | None = None,
    ) -> None:
        self._reader = knowledge_reader
        self._scorer = priority_scorer or PriorityScorer()

    def build_candidates(
        self,
        tenant_id: str,
        *,
        reference_at: datetime | None = None,
    ) -> list[RecommendationCandidate]:
        ref = reference_at or datetime.now(timezone.utc)
        snapshot = self._reader.read(tenant_id)
        candidates = evaluate_all_rules(snapshot, reference_at=ref)
        return self._scorer.score_and_sort(candidates, snapshot, reference_at=ref)
