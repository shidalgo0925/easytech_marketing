"""ContentBuilder — plan + campaña → ContentPiece estructurada."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_BUILDER_VERSION
from Motor_Tecnico.accio_engine.content_engine_domain.content_planner import ContentPlan, ContentPlanItem
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_content_id(campaign_id: str) -> str:
    digest = secrets.token_hex(3)
    safe = campaign_id.replace(":", "_")[:16]
    return f"cnt_{safe}_{digest}"


class ContentBuilder:
    def build(
        self,
        tenant_id: str,
        campaign: Campaign,
        plan: ContentPlan,
        item: ContentPlanItem,
        *,
        content_id: str | None = None,
    ) -> ContentPiece:
        now = _utc_now()
        headline = f"{campaign.name} — {item.objective[:80]}".strip(" —")
        body = self._body_template(campaign, item)
        cta = campaign.call_to_action or "DIAGNÓSTICO"
        hashtags = self._hashtags(campaign)

        return ContentPiece(
            tenant_id=tenant_id,
            content_id=content_id or new_content_id(campaign.campaign_id),
            brand_id=campaign.brand_id,
            title=f"{campaign.name} · {item.channel}",
            format=item.format,
            channel=item.channel,
            content_type=item.content_type,
            status="draft",
            headline=headline,
            body=body,
            call_to_action=cta,
            hashtags=hashtags,
            flyer_ref=item.suggested_flyer or "",
            objective=item.objective,
            campaign_id=campaign.campaign_id,
            recommendation_id=campaign.recommendation_id,
            planner_version=plan.planner_version,
            builder_version=CONTENT_BUILDER_VERSION,
            created_at=now,
            updated_at=now,
            payload={
                "campaign_type": campaign.campaign_type,
                "target_audience": campaign.target_audience,
                "value_proposition": campaign.value_proposition,
            },
        )

    def _body_template(self, campaign: Campaign, item: ContentPlanItem) -> str:
        lines = [
            f"Objetivo: {item.objective}",
            f"Propuesta: {campaign.value_proposition or campaign.description}",
            f"Audiencia: {campaign.target_audience or 'B2B Panamá/LATAM'}",
            f"CTA: {campaign.call_to_action or 'DIAGNÓSTICO'}",
        ]
        return "\n".join(lines)

    def _hashtags(self, campaign: Campaign) -> tuple[str, ...]:
        slug = (campaign.product_ref or campaign.brand_id or "easytech").replace(" ", "")
        tags = ["#B2B", "#Panama", f"#{slug}"]
        if campaign.campaign_type == "awareness":
            tags.append("#TransformacionDigital")
        return tuple(tags[:5])
