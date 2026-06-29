from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Publication:
    tenant_id: str
    publication_id: str
    brand_id: str
    channel: str
    body: str
    status: str = "scheduled"
    title: str = ""
    scheduled_at: str = ""
    published_at: str = ""
    external_post_id: str = ""
    flyer_ref: str = ""
    campaign_id: str = ""
    legacy_queue_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "publication_id": self.publication_id,
            "id": self.legacy_queue_id or self.publication_id,
            "tenant_id": self.tenant_id,
            "app_id": self.brand_id,
            "brand_id": self.brand_id,
            "platform": self.channel,
            "channel": self.channel,
            "text": self.body,
            "body": self.body,
            "title": self.title,
            "status": self.status,
            "scheduled_at": self.scheduled_at,
            "published_at": self.published_at,
            "external_post_id": self.external_post_id,
            "flyer": self.flyer_ref,
            "campaign_id": self.campaign_id,
            "legacy_queue_id": self.legacy_queue_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row
