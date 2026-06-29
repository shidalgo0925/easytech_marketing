#!/usr/bin/env python3
"""Registro local de leads con tenant_id, app_id y atribución."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import resolve_tenant


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def leads_path(tenant_id: str) -> Path:
    return resolve_tenant(tenant_id).root / "leads.json"


def load_leads(tenant_id: str) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.lead_infrastructure.facade import lead_store_active, load_leads as facade_load

    if lead_store_active():
        return facade_load(tenant_id)

    path = leads_path(tenant_id)
    if not path.is_file():
        return {"version": 1, "leads": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_leads(data: dict[str, Any], tenant_id: str) -> None:
    from Motor_Tecnico.accio_engine.lead_infrastructure.facade import lead_store_active, save_leads as facade_save

    if lead_store_active():
        facade_save(data, tenant_id)
        return

    path = leads_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record_lead(
    tenant_id: str,
    *,
    app_id: str = "default",
    campaign_id: str = "",
    source: str = "",
    medium: str = "",
    channel: str = "",
    landing_url: str = "",
    utm: dict[str, str] | None = None,
    status: str = "new",
    crm_destination: str = "",
    crm_lead_id: str | int | None = None,
    contact: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.lead_infrastructure.facade import append_lead, lead_store_active

    entry = {
        "id": f"lead_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "app_id": app_id,
        "campaign_id": campaign_id,
        "source": source,
        "medium": medium,
        "channel": channel,
        "landing_url": landing_url,
        "utm": utm or {},
        "status": status,
        "crm_destination": crm_destination,
        "crm_lead_id": crm_lead_id,
        "contact": contact or {},
        "meta": meta or {},
        "created_at": _utc_now(),
    }
    if lead_store_active():
        return append_lead(tenant_id, entry)

    data = load_leads(tenant_id)
    data.setdefault("leads", []).append(entry)
    save_leads(data, tenant_id)
    return entry


def list_leads(
    tenant_id: str,
    *,
    app_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from Motor_Tecnico.accio_engine.lead_infrastructure.facade import lead_store_active, list_leads as facade_list

    if lead_store_active():
        return facade_list(tenant_id, app_id=app_id, limit=limit)

    items = load_leads(tenant_id).get("leads", [])
    if app_id:
        items = [x for x in items if x.get("app_id") == app_id]
    return sorted(items, key=lambda x: x.get("created_at") or "", reverse=True)[:limit]
