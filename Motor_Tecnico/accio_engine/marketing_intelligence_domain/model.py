from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OPPORTUNITY_SCORER_VERSION = "opportunity_scorer_v1"
RECOMMENDATION_COMPOSER_VERSION = "recommendation_composer_v1"
EXPLAINABILITY_VERSION = "explainability_v1"


def priority_from_score_100(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def resolve_opportunity_priority(rule_priority: str, score: float) -> str:
    """Combina prioridad de regla y score; nunca degrada la regla."""
    order = {"low": 0, "medium": 1, "high": 2}
    score_prio = priority_from_score_100(score)
    rule = rule_priority if rule_priority in order else "medium"
    return rule if order[rule] >= order[score_prio] else score_prio


@dataclass(frozen=True)
class OpportunityScoreResult:
    score: float
    confidence: float
    priority: str
    reasoning: tuple[str, ...]
    factors: dict[str, float]
    algorithm_version: str = OPPORTUNITY_SCORER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "confidence": round(self.confidence, 3),
            "priority": self.priority,
            "reasoning": list(self.reasoning),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "algorithm_version": self.algorithm_version,
        }


@dataclass(frozen=True)
class ComposedRecommendation:
    title: str
    description: str
    objective: str
    expected_impact: str
    recommended_action: str
    priority: str
    reasons: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]
    next_steps: tuple[str, ...]
    composer_version: str = RECOMMENDATION_COMPOSER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "objective": self.objective,
            "expected_impact": self.expected_impact,
            "recommended_action": self.recommended_action,
            "priority": self.priority,
            "reasons": list(self.reasons),
            "evidence": list(self.evidence),
            "next_steps": list(self.next_steps),
            "composer_version": self.composer_version,
        }


@dataclass(frozen=True)
class RecommendationExplain:
    algorithm_version: str
    generated_at: str
    rules_triggered: tuple[dict[str, Any], ...]
    data_used: dict[str, Any]
    score: float
    factors: dict[str, float]
    context_considered: tuple[str, ...]
    reasoning: tuple[str, ...]
    composed: dict[str, Any]
    opportunity_id: str | None = None
    signal_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm_version": self.algorithm_version,
            "generated_at": self.generated_at,
            "rules_triggered": list(self.rules_triggered),
            "data_used": self.data_used,
            "score": round(self.score, 2),
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "context_considered": list(self.context_considered),
            "reasoning": list(self.reasoning),
            "composed": self.composed,
            "opportunity_id": self.opportunity_id,
            "signal_type": self.signal_type,
        }
