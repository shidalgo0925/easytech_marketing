"""CampaignBuilder — recomendación + plan → Campaign estructurada."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.campaign_domain.campaign_planner import CampaignPlan
from Motor_Tecnico.accio_engine.campaign_domain.constants import CAMPAIGN_BUILDER_VERSION
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_campaign_id(recommendation_id: str) -> str:
    digest = secrets.token_hex(3)
    safe = recommendation_id.replace(":", "_")[:16]
    return f"cmp_{safe}_{digest}"


class CampaignBuilder:
    def build(
        self,
        tenant_id: str,
        recommendation: Recommendation,
        plan: CampaignPlan,
        *,
        campaign_id: str | None = None,
        origin_score: float | None = None,
    ) -> Campaign:
        refs = recommendation.justification_refs or {}
        composed = recommendation.composed or {}
        now = _utc_now()
        primary_channel = plan.channels[0].channel if plan.channels else "linkedin"

        description = str(
            composed.get("description") or recommendation.description or recommendation.title
        ).strip()
        value_prop = str(
            composed.get("expected_impact")
            or recommendation.expected_roi
            or plan.objective
        ).strip()

        return Campaign(
            tenant_id=tenant_id,
            campaign_id=campaign_id or new_campaign_id(recommendation.recommendation_id),
            brand_id=recommendation.brand_id,
            name=str(composed.get("title") or recommendation.title).strip(),
            product_ref=str(refs.get("product_slug") or recommendation.brand_id),
            channel=primary_channel,
            status="draft",
            objective=plan.objective,
            start_at=plan.start_date,
            end_at=plan.end_date,
            created_at=now,
            updated_at=now,
            recommendation_id=recommendation.recommendation_id,
            opportunity_id=str(refs.get("opportunity_id") or "") or None,
            description=description,
            target_audience=plan.target_audience,
            value_proposition=value_prop,
            call_to_action=plan.call_to_action,
            priority=plan.priority,
            owner=recommendation.owner_role or "marketing",
            start_date=plan.start_date,
            end_date=plan.end_date,
            estimated_reach=plan.estimated_reach,
            estimated_leads=plan.estimated_leads,
            estimated_conversion=plan.estimated_conversion,
            campaign_type=plan.campaign_type,
            frequency=plan.frequency,
            channels=plan.channels,
            kpis=plan.kpis,
            origin_score=origin_score,
            planner_version=plan.planner_version,
            builder_version=CAMPAIGN_BUILDER_VERSION,
            payload={
                "source_recommendation_action": recommendation.action,
                "source_recommendation_source": recommendation.source,
            },
        )
