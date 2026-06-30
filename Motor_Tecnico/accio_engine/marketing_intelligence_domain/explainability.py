"""Explainability — trazabilidad técnica de recomendaciones."""

from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.model import (
    EXPLAINABILITY_VERSION,
    ComposedRecommendation,
    OpportunityScoreResult,
    RecommendationExplain,
)
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_explain(
    *,
    opportunity: Opportunity | None,
    score: OpportunityScoreResult,
    composed: ComposedRecommendation,
    context_keys: tuple[str, ...] = (),
    data_used: dict | None = None,
) -> RecommendationExplain:
    rules = []
    if opportunity:
        rules.append(
            {
                "rule_id": opportunity.signal_type,
                "signal_key": opportunity.signal_key,
                "source": opportunity.source,
                "brand_id": opportunity.brand_id,
            }
        )
    return RecommendationExplain(
        algorithm_version=EXPLAINABILITY_VERSION,
        generated_at=_utc_now(),
        rules_triggered=tuple(rules),
        data_used=data_used or {
            "payload": dict(opportunity.payload or {}) if opportunity else {},
            "sector": opportunity.sector if opportunity else None,
            "product_slug": opportunity.product_slug if opportunity else None,
        },
        score=score.score,
        factors=dict(score.factors),
        context_considered=context_keys,
        reasoning=score.reasoning,
        composed=composed.to_dict(),
        opportunity_id=opportunity.opportunity_id if opportunity else None,
        signal_type=opportunity.signal_type if opportunity else None,
    )


def explain_from_recommendation(rec: Recommendation) -> dict | None:
    if rec.explain:
        return rec.explain
    refs = rec.justification_refs or {}
    if not refs.get("opportunity_id") and not refs.get("signal_type"):
        return None
    return {
        "algorithm_version": EXPLAINABILITY_VERSION,
        "generated_at": rec.created_at,
        "rules_triggered": [{"rule_id": refs.get("signal_type"), "signal_key": refs.get("signal_key")}],
        "data_used": refs,
        "score": refs.get("opportunity_score", rec.priority_score * 100),
        "factors": refs.get("score_factors", {}),
        "context_considered": [],
        "reasoning": [rec.reason],
        "composed": rec.composed or {"title": rec.title, "description": rec.description},
        "opportunity_id": refs.get("opportunity_id"),
        "signal_type": refs.get("signal_type"),
        "note": "reconstructed_from_refs",
    }


def similarity_key(rec: Recommendation) -> tuple:
    refs = rec.justification_refs or {}
    return (
        rec.brand_id,
        rec.action,
        refs.get("signal_type") or rec.source,
        rec.priority,
    )
