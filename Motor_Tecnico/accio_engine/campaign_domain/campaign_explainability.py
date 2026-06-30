"""Campaign explainability — trazabilidad de por qué existe una campaña."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.campaign_planner import CampaignPlan
from Motor_Tecnico.accio_engine.campaign_domain.constants import CAMPAIGN_EXPLAIN_VERSION
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity


def build_campaign_explain(
    *,
    campaign: Campaign,
    recommendation: Recommendation,
    plan: CampaignPlan,
    opportunity: Opportunity | None = None,
    marketing_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    explain_rec = recommendation.explain or {}
    composed = recommendation.composed or {}
    refs = recommendation.justification_refs or {}

    rules_triggered: list[dict[str, Any]] = []
    if explain_rec.get("rules_triggered"):
        rules_triggered = list(explain_rec["rules_triggered"])
    elif recommendation.source:
        rules_triggered = [{"type": "source", "id": recommendation.source, "label": recommendation.source}]

    score = campaign.origin_score
    if score is None and explain_rec.get("score") is not None:
        score = float(explain_rec["score"])

    motor_reasoning: list[str] = list(explain_rec.get("reasoning") or composed.get("reasons") or [])
    if plan.objective and plan.objective not in motor_reasoning:
        motor_reasoning.insert(0, plan.objective)

    return {
        "algorithm_version": CAMPAIGN_EXPLAIN_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "recommendation_id": recommendation.recommendation_id,
        "opportunity_id": campaign.opportunity_id or refs.get("opportunity_id"),
        "score": score,
        "factors": explain_rec.get("factors") or refs.get("score_factors") or {},
        "rules_triggered": rules_triggered,
        "context_considered": list(plan.context_used),
        "objectives": [plan.objective],
        "motor_reasoning": motor_reasoning,
        "ai_enrichment": campaign.llm_enrichment,
        "data_used": {
            "recommendation_action": recommendation.action,
            "recommendation_priority": recommendation.priority,
            "campaign_type": plan.campaign_type,
            "channels": [c.channel for c in plan.channels],
            "opportunity_signal": opportunity.signal_type if opportunity else None,
            "marketing_context_keys": sorted((marketing_context or {}).keys()),
        },
        "planner": plan.to_dict(),
    }


def explain_from_campaign(campaign: Campaign) -> dict[str, Any] | None:
    return campaign.explain
