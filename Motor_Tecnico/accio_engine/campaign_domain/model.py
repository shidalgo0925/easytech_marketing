from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.constants import ENGINE_CAMPAIGN_STATUSES


@dataclass(frozen=True)
class CampaignChannel:
    channel: str
    role: str = "primary"
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CampaignKpi:
    kpi_id: str
    name: str
    target_value: float | None = None
    unit: str = ""


@dataclass(frozen=True)
class Campaign:
    tenant_id: str
    campaign_id: str
    brand_id: str
    name: str
    post_id: str = ""
    product_ref: str = ""
    channel: str = ""
    status: str = "active"
    objective: str = ""
    start_at: str = ""
    end_at: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    # Campaign Engine fields
    recommendation_id: str | None = None
    opportunity_id: str | None = None
    description: str = ""
    target_audience: str = ""
    value_proposition: str = ""
    call_to_action: str = ""
    priority: str = "medium"
    owner: str = "marketing"
    start_date: str = ""
    end_date: str = ""
    budget: float | None = None
    estimated_reach: int | None = None
    estimated_leads: int | None = None
    estimated_conversion: float | None = None
    campaign_type: str = ""
    frequency: str = ""
    channels: tuple[CampaignChannel, ...] = ()
    kpis: tuple[CampaignKpi, ...] = ()
    explain: dict[str, Any] | None = None
    llm_enrichment: dict[str, Any] | None = None
    llm_skipped: bool = False
    origin_score: float | None = None
    planner_version: str = ""
    builder_version: str = ""

    @property
    def title(self) -> str:
        return self.name

    @property
    def is_engine_campaign(self) -> bool:
        return bool(self.recommendation_id) or self.status in ENGINE_CAMPAIGN_STATUSES

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "campaign_id": self.campaign_id,
            "id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "name": self.name,
            "title": self.name,
            "product": self.product_ref or self.name,
            "post_id": self.post_id,
            "channel": self.channel,
            "status": self.status,
            "objective": self.objective,
            "start_at": self.start_at or self.start_date,
            "end_at": self.end_at or self.end_date,
            "start_date": self.start_date or self.start_at,
            "end_date": self.end_date or self.end_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "recommendation_id": self.recommendation_id,
            "opportunity_id": self.opportunity_id,
            "description": self.description,
            "target_audience": self.target_audience,
            "value_proposition": self.value_proposition,
            "call_to_action": self.call_to_action,
            "priority": self.priority,
            "owner": self.owner,
            "budget": self.budget,
            "estimated_reach": self.estimated_reach,
            "estimated_leads": self.estimated_leads,
            "estimated_conversion": self.estimated_conversion,
            "campaign_type": self.campaign_type,
            "frequency": self.frequency,
            "channels": [
                {"channel": c.channel, "role": c.role, "config": c.config} for c in self.channels
            ],
            "kpis": [
                {
                    "kpi_id": k.kpi_id,
                    "name": k.name,
                    "target_value": k.target_value,
                    "unit": k.unit,
                }
                for k in self.kpis
            ],
            "explain": self.explain,
            "llm_enrichment": self.llm_enrichment,
            "llm_skipped": self.llm_skipped,
            "origin_score": self.origin_score,
            "planner_version": self.planner_version,
            "builder_version": self.builder_version,
            "is_engine_campaign": self.is_engine_campaign,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row

    def to_legacy_dict(self) -> dict[str, Any]:
        row = {
            "id": self.campaign_id,
            "post_id": self.post_id,
            "product": self.product_ref or self.name,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row
