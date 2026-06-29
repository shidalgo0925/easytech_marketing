"""Legacy leads.json ↔ Lead."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.lead_domain.model import Lead

_CORE_KEYS = frozenset(
    {
        "id",
        "tenant_id",
        "app_id",
        "brand_id",
        "source",
        "medium",
        "channel",
        "campaign_id",
        "landing_url",
        "status",
        "crm_destination",
        "crm_lead_id",
        "contact",
        "created_at",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def legacy_row_to_lead(tenant_id: str, row: dict[str, Any]) -> Lead:
    lead_id = str(row.get("id") or row.get("lead_id") or "")
    brand_id = str(row.get("app_id") or row.get("brand_id") or marketing_app.DEFAULT_APP_ID)
    payload = {k: v for k, v in row.items() if k not in _CORE_KEYS and v is not None}
    now = _utc_now()
    return Lead(
        tenant_id=tenant_id,
        lead_id=lead_id,
        brand_id=brand_id,
        status=str(row.get("status") or "new"),
        source=str(row.get("source") or ""),
        medium=str(row.get("medium") or ""),
        channel=str(row.get("channel") or ""),
        campaign_id=str(row.get("campaign_id") or ""),
        landing_url=str(row.get("landing_url") or ""),
        crm_destination=str(row.get("crm_destination") or ""),
        crm_lead_id=str(row.get("crm_lead_id") or "") if row.get("crm_lead_id") is not None else "",
        contact=dict(row.get("contact") or {}),
        payload=payload,
        created_at=str(row.get("created_at") or now),
        updated_at=now,
    )


def catalog_to_leads(tenant_id: str, data: dict[str, Any]) -> list[Lead]:
    return [legacy_row_to_lead(tenant_id, row) for row in data.get("leads", []) if row.get("id") or row.get("lead_id")]


def leads_to_catalog(leads: list[Lead]) -> dict[str, Any]:
    return {"version": 1, "leads": [lead.to_api_dict() for lead in leads]}


def lead_to_row(lead: Lead) -> dict[str, Any]:
    return {
        "tenant_id": lead.tenant_id,
        "lead_id": lead.lead_id,
        "brand_id": lead.brand_id,
        "source": lead.source,
        "medium": lead.medium,
        "channel": lead.channel,
        "campaign_id": lead.campaign_id,
        "landing_url": lead.landing_url,
        "status": lead.status,
        "crm_destination": lead.crm_destination,
        "crm_lead_id": lead.crm_lead_id,
        "contact_json": json.dumps(lead.contact or {}, ensure_ascii=False),
        "payload_json": json.dumps(lead.payload or {}, ensure_ascii=False),
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
    }


def row_to_lead(row: Any) -> Lead:
    return Lead(
        tenant_id=row["tenant_id"],
        lead_id=row["lead_id"],
        brand_id=row["brand_id"],
        status=row["status"],
        source=row["source"] or "",
        medium=row["medium"] or "",
        channel=row["channel"] or "",
        campaign_id=row["campaign_id"] or "",
        landing_url=row["landing_url"] or "",
        crm_destination=row["crm_destination"] or "",
        crm_lead_id=row["crm_lead_id"] or "",
        contact=json.loads(row["contact_json"] or "{}"),
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
