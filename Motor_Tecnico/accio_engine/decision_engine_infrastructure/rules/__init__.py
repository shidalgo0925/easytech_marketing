from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot

from .brand_publication_gap import evaluate_brand_publication_gap

RuleEvaluator = Callable[..., list[RecommendationCandidate]]

ENABLED_RULES: tuple[RuleEvaluator, ...] = (evaluate_brand_publication_gap,)


def evaluate_all_rules(
    snapshot: KnowledgeSnapshot,
    *,
    reference_at: datetime | None = None,
) -> list[RecommendationCandidate]:
    ref = reference_at or datetime.now(timezone.utc)
    candidates: list[RecommendationCandidate] = []
    for rule in ENABLED_RULES:
        candidates.extend(rule(snapshot, reference_at=ref))
    return candidates
