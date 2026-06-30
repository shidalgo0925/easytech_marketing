"""Map Opportunity → Decision Engine RecommendationCandidate."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity

_ACTION_BY_SIGNAL = {
    "brand_inactive": "create_publication",
    "campaign_stalled": "resume_campaign",
    "lead_followup_gap": "follow_up_lead",
}

_PRIORITY_SCORE = {"high": 0.8, "medium": 0.55, "low": 0.3}


def opportunity_to_candidate(opportunity: Opportunity) -> RecommendationCandidate:
    action = _ACTION_BY_SIGNAL.get(opportunity.signal_type, "review_opportunity")
    refs = {
        "opportunity_id": opportunity.opportunity_id,
        "signal_key": opportunity.signal_key,
        "signal_type": opportunity.signal_type,
        "product_slug": opportunity.product_slug,
        "sector": opportunity.sector,
        "channel": opportunity.channel,
        "landing_url": opportunity.landing_url,
    }
    refs.update(opportunity.payload or {})
    return RecommendationCandidate(
        brand_id=opportunity.brand_id,
        title=opportunity.title,
        description=opportunity.description,
        action=action,
        reason=opportunity.need or opportunity.description,
        priority=opportunity.priority,
        priority_score=_PRIORITY_SCORE.get(opportunity.priority, 0.5),
        owner_role="marketing",
        source=f"opportunity:{opportunity.signal_type}",
        confidence=opportunity.confidence,
        justification_refs=refs,
    )
