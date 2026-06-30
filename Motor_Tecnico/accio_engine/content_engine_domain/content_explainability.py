"""Content explainability — ¿por qué este contenido?"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_EXPLAIN_VERSION
from Motor_Tecnico.accio_engine.content_engine_domain.content_planner import ContentPlan
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece


def build_content_explain(
    *,
    content: ContentPiece,
    campaign: Campaign,
    plan: ContentPlan,
) -> dict[str, Any]:
    campaign_explain = campaign.explain or {}
    return {
        "algorithm_version": CONTENT_EXPLAIN_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "campaign_id": campaign.campaign_id,
        "recommendation_id": campaign.recommendation_id,
        "origin_score": campaign.origin_score,
        "campaign_explain": campaign_explain,
        "content_plan": plan.to_dict(),
        "context_considered": list(plan.context_used),
        "motor_reasoning": [
            f"Formato «{content.format}» para canal «{content.channel}»",
            f"Tipo editorial «{content.content_type}» según campaña «{campaign.campaign_type}»",
            f"Objetivo de campaña: {campaign.objective}",
        ],
        "objectives": [content.objective],
        "rules_triggered": list(campaign_explain.get("rules_triggered") or []),
        "ai_enrichment": content.llm_enrichment,
    }
