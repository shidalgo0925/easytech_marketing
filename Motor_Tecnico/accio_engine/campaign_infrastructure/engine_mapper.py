"""Engine campaign mappers — SQLite ↔ Campaign."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign, CampaignChannel, CampaignKpi


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _channels_from_json(raw: str | None) -> tuple[CampaignChannel, ...]:
    if not raw:
        return ()
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(rows, list):
        return ()
    out: list[CampaignChannel] = []
    for row in rows:
        if isinstance(row, dict) and row.get("channel"):
            out.append(
                CampaignChannel(
                    str(row["channel"]),
                    str(row.get("role") or "primary"),
                    dict(row.get("config") or {}),
                )
            )
    return tuple(out)


def _kpis_from_json(raw: str | None) -> tuple[CampaignKpi, ...]:
    if not raw:
        return ()
    try:
        rows = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(rows, list):
        return ()
    out: list[CampaignKpi] = []
    for row in rows:
        if isinstance(row, dict) and row.get("kpi_id"):
            out.append(
                CampaignKpi(
                    str(row["kpi_id"]),
                    str(row.get("name") or row["kpi_id"]),
                    float(row["target_value"]) if row.get("target_value") is not None else None,
                    str(row.get("unit") or ""),
                )
            )
    return tuple(out)


def campaign_to_row(campaign: Campaign) -> dict[str, Any]:
    channels = [
        {"channel": c.channel, "role": c.role, "config": c.config} for c in campaign.channels
    ]
    kpis = [
        {
            "kpi_id": k.kpi_id,
            "name": k.name,
            "target_value": k.target_value,
            "unit": k.unit,
        }
        for k in campaign.kpis
    ]
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
        "start_at": campaign.start_at or campaign.start_date,
        "end_at": campaign.end_at or campaign.end_date,
        "payload_json": json.dumps(campaign.payload or {}, ensure_ascii=False),
        "created_at": campaign.created_at or _utc_now(),
        "updated_at": campaign.updated_at or _utc_now(),
        "recommendation_id": campaign.recommendation_id,
        "opportunity_id": campaign.opportunity_id,
        "description": campaign.description,
        "target_audience": campaign.target_audience,
        "value_proposition": campaign.value_proposition,
        "call_to_action": campaign.call_to_action,
        "priority": campaign.priority,
        "owner": campaign.owner,
        "start_date": campaign.start_date or campaign.start_at,
        "end_date": campaign.end_date or campaign.end_at,
        "budget": campaign.budget,
        "estimated_reach": campaign.estimated_reach,
        "estimated_leads": campaign.estimated_leads,
        "estimated_conversion": campaign.estimated_conversion,
        "campaign_type": campaign.campaign_type,
        "frequency": campaign.frequency,
        "channels_json": json.dumps(channels, ensure_ascii=False),
        "kpis_json": json.dumps(kpis, ensure_ascii=False),
        "explain_json": json.dumps(campaign.explain or {}, ensure_ascii=False) if campaign.explain else None,
        "llm_enrichment_json": json.dumps(campaign.llm_enrichment or {}, ensure_ascii=False)
        if campaign.llm_enrichment
        else None,
        "llm_skipped": 1 if campaign.llm_skipped else 0,
        "planner_version": campaign.planner_version,
        "builder_version": campaign.builder_version,
        "origin_score": campaign.origin_score,
    }


def row_to_campaign(row: Any) -> Campaign:
    keys = row.keys() if hasattr(row, "keys") else []
    explain = None
    if "explain_json" in keys and row["explain_json"]:
        explain = json.loads(row["explain_json"])
    llm = None
    if "llm_enrichment_json" in keys and row["llm_enrichment_json"]:
        llm = json.loads(row["llm_enrichment_json"])
    channels = _channels_from_json(row["channels_json"] if "channels_json" in keys else None)
    kpis = _kpis_from_json(row["kpis_json"] if "kpis_json" in keys else None)
    if not channels and row["channel"]:
        channels = (CampaignChannel(str(row["channel"]), "primary"),)
    return Campaign(
        tenant_id=row["tenant_id"],
        campaign_id=row["campaign_id"],
        brand_id=row["brand_id"],
        name=row["name"],
        post_id=row["post_id"] or "",
        product_ref=row["product_ref"] or "",
        channel=row["channel"] or "",
        status=row["status"],
        objective=row["objective"] or "",
        start_at=row["start_at"] or "",
        end_at=row["end_at"] or "",
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        recommendation_id=row["recommendation_id"] if "recommendation_id" in keys else None,
        opportunity_id=row["opportunity_id"] if "opportunity_id" in keys else None,
        description=row["description"] if "description" in keys and row["description"] else "",
        target_audience=row["target_audience"] if "target_audience" in keys and row["target_audience"] else "",
        value_proposition=row["value_proposition"] if "value_proposition" in keys and row["value_proposition"] else "",
        call_to_action=row["call_to_action"] if "call_to_action" in keys and row["call_to_action"] else "",
        priority=row["priority"] if "priority" in keys and row["priority"] else "medium",
        owner=row["owner"] if "owner" in keys and row["owner"] else "marketing",
        start_date=row["start_date"] if "start_date" in keys and row["start_date"] else "",
        end_date=row["end_date"] if "end_date" in keys and row["end_date"] else "",
        budget=float(row["budget"]) if "budget" in keys and row["budget"] is not None else None,
        estimated_reach=int(row["estimated_reach"]) if "estimated_reach" in keys and row["estimated_reach"] is not None else None,
        estimated_leads=int(row["estimated_leads"]) if "estimated_leads" in keys and row["estimated_leads"] is not None else None,
        estimated_conversion=float(row["estimated_conversion"])
        if "estimated_conversion" in keys and row["estimated_conversion"] is not None
        else None,
        campaign_type=row["campaign_type"] if "campaign_type" in keys and row["campaign_type"] else "",
        frequency=row["frequency"] if "frequency" in keys and row["frequency"] else "",
        channels=channels,
        kpis=kpis,
        explain=explain,
        llm_enrichment=llm,
        llm_skipped=bool(row["llm_skipped"]) if "llm_skipped" in keys else False,
        origin_score=float(row["origin_score"]) if "origin_score" in keys and row["origin_score"] is not None else None,
        planner_version=row["planner_version"] if "planner_version" in keys and row["planner_version"] else "",
        builder_version=row["builder_version"] if "builder_version" in keys and row["builder_version"] else "",
    )
