from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Lead:
    tenant_id: str
    lead_id: str
    brand_id: str
    status: str = "new"
    source: str = ""
    medium: str = ""
    channel: str = ""
    campaign_id: str = ""
    landing_url: str = ""
    crm_destination: str = ""
    crm_lead_id: str = ""
    contact: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "id": self.lead_id,
            "lead_id": self.lead_id,
            "tenant_id": self.tenant_id,
            "app_id": self.brand_id,
            "brand_id": self.brand_id,
            "source": self.source,
            "medium": self.medium,
            "channel": self.channel,
            "campaign_id": self.campaign_id,
            "landing_url": self.landing_url,
            "status": self.status,
            "crm_destination": self.crm_destination,
            "crm_lead_id": self.crm_lead_id,
            "contact": self.contact,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row
