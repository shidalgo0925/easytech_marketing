"""ContentPlanner — campaña aprobada → plan de piezas de contenido."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_PLANNER_VERSION

_TYPE_BY_CAMPAIGN = {
    "awareness": "valor",
    "conversion": "venta",
    "retention": "valor",
    "growth": "valor",
}


@dataclass(frozen=True)
class ContentPlanItem:
    format: str
    channel: str
    content_type: str
    objective: str
    suggested_flyer: str | None = None


@dataclass(frozen=True)
class ContentPlan:
    items: tuple[ContentPlanItem, ...]
    context_used: tuple[str, ...]
    planner_version: str = CONTENT_PLANNER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [
                {
                    "format": i.format,
                    "channel": i.channel,
                    "content_type": i.content_type,
                    "objective": i.objective,
                    "suggested_flyer": i.suggested_flyer,
                }
                for i in self.items
            ],
            "context_used": list(self.context_used),
            "planner_version": self.planner_version,
        }


class ContentPlanner:
    def plan(self, campaign: Campaign, *, marketing_context: dict[str, Any] | None = None) -> ContentPlan:
        content_type = _TYPE_BY_CAMPAIGN.get(campaign.campaign_type, "valor")
        if campaign.campaign_type == "conversion":
            content_type = "venta"

        channel = campaign.channel or "linkedin"
        if campaign.channels:
            channel = campaign.channels[0].channel

        objective = campaign.objective or campaign.description or campaign.name
        flyer = (campaign.payload or {}).get("flyer_num") or campaign.product_ref or ""

        items = (
            ContentPlanItem(
                format="post",
                channel=channel,
                content_type=content_type,
                objective=objective,
                suggested_flyer=str(flyer) if flyer else None,
            ),
        )

        labels: list[str] = ["campaign_structure"]
        if campaign.explain:
            labels.append("campaign_explain")
        if marketing_context:
            if marketing_context.get("company_brain"):
                labels.append("company_brain")
            if marketing_context.get("recent_publications"):
                labels.append("recent_publications")

        return ContentPlan(items=items, context_used=tuple(labels))
