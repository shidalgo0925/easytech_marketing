from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "campaign_id": self.campaign_id,
            "id": self.campaign_id,
            "tenant_id": self.tenant_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "name": self.name,
            "product": self.product_ref or self.name,
            "post_id": self.post_id,
            "channel": self.channel,
            "status": self.status,
            "objective": self.objective,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
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
