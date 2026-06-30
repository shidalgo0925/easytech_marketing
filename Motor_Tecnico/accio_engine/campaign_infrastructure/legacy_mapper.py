"""Legacy campaigns.json ↔ Campaign."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign

_CORE_KEYS = frozenset(
    {
        "id",
        "post_id",
        "product",
        "name",
        "channel",
        "status",
        "objective",
        "start_at",
        "end_at",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def legacy_row_to_campaign(tenant_id: str, brand_id: str, row: dict[str, Any]) -> Campaign:
    campaign_id = str(row.get("id") or row.get("post_id") or "")
    if not campaign_id:
        raise ValueError("Campaña sin id")
    product_ref = str(row.get("product") or row.get("name") or campaign_id)
    payload = {k: v for k, v in row.items() if k not in _CORE_KEYS and v is not None}
    now = _utc_now()
    return Campaign(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        brand_id=brand_id,
        name=product_ref,
        post_id=str(row.get("post_id") or ""),
        product_ref=product_ref,
        channel=str(row.get("channel") or ""),
        status=str(row.get("status") or "active"),
        objective=str(row.get("objective") or ""),
        start_at=str(row.get("start_at") or ""),
        end_at=str(row.get("end_at") or ""),
        payload=payload,
        created_at=now,
        updated_at=now,
    )


def store_to_campaigns(tenant_id: str, brand_id: str, data: dict[str, Any]) -> list[Campaign]:
    return [legacy_row_to_campaign(tenant_id, brand_id, row) for row in data.get("campaigns", [])]


def campaigns_to_store(campaigns: list[Campaign], *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(meta or {})
    data.setdefault("version", 1)
    data["updated_at"] = _utc_now()[:10]
    data["campaigns"] = [c.to_legacy_dict() for c in campaigns]
    return data


def campaign_to_row(campaign: Campaign) -> dict[str, Any]:
    return {
        "tenant_id": campaign.tenant_id,
        "campaign_id": campaign.campaign_id,
        "brand_id": campaign.brand_id,
        "name": campaign.name,
        "post_id": campaign.post_id,
        "product_ref": campaign.product_ref,
        "channel": campaign.channel,
        "status": campaign.status,
        "objective": campaign.objective,
        "start_at": campaign.start_at,
        "end_at": campaign.end_at,
        "payload_json": json.dumps(campaign.payload or {}, ensure_ascii=False),
        "created_at": campaign.created_at,
        "updated_at": campaign.updated_at,
    }


def row_to_campaign(row: Any) -> Campaign:
    from Motor_Tecnico.accio_engine.campaign_infrastructure.engine_mapper import row_to_campaign as _engine_row

    return _engine_row(row)
