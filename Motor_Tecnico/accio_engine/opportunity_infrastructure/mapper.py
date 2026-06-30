from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity, OpportunityCandidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_opportunity_id(signal_key: str) -> str:
    digest = secrets.token_hex(3)
    safe = signal_key.replace(":", "_")[:24]
    return f"opp_{safe}_{digest}"


def candidate_to_opportunity(tenant_id: str, candidate: OpportunityCandidate) -> Opportunity:
    now = _utc_now()
    return Opportunity(
        tenant_id=tenant_id,
        opportunity_id=new_opportunity_id(candidate.signal_key),
        signal_key=candidate.signal_key,
        signal_type=candidate.signal_type,
        brand_id=candidate.brand_id,
        title=candidate.title,
        description=candidate.description,
        sector=candidate.sector,
        need=candidate.need,
        product_slug=candidate.product_slug,
        channel=candidate.channel,
        landing_url=candidate.landing_url,
        priority=candidate.priority,
        status="detected",
        source=candidate.source,
        confidence=candidate.confidence,
        detected_at=now,
        updated_at=now,
        payload=dict(candidate.payload or {}),
    )


def opportunity_to_row(opportunity: Opportunity) -> dict[str, Any]:
    return {
        "tenant_id": opportunity.tenant_id,
        "opportunity_id": opportunity.opportunity_id,
        "signal_key": opportunity.signal_key,
        "signal_type": opportunity.signal_type,
        "brand_id": opportunity.brand_id,
        "title": opportunity.title,
        "description": opportunity.description,
        "sector": opportunity.sector,
        "need": opportunity.need,
        "product_slug": opportunity.product_slug,
        "channel": opportunity.channel,
        "landing_url": opportunity.landing_url,
        "priority": opportunity.priority,
        "status": opportunity.status,
        "confidence": opportunity.confidence,
        "source": opportunity.source,
        "payload_json": json.dumps(opportunity.payload or {}, ensure_ascii=False),
        "detected_at": opportunity.detected_at,
        "updated_at": opportunity.updated_at,
    }


def row_to_opportunity(row: Any) -> Opportunity:
    return Opportunity(
        tenant_id=row["tenant_id"],
        opportunity_id=row["opportunity_id"],
        signal_key=row["signal_key"],
        signal_type=row["signal_type"],
        brand_id=row["brand_id"] or "",
        title=row["title"],
        description=row["description"] or "",
        sector=row["sector"] or "",
        need=row["need"] or "",
        product_slug=row["product_slug"] or "",
        channel=row["channel"] or "",
        landing_url=row["landing_url"] or "",
        priority=row["priority"],
        status=row["status"],
        source=row["source"],
        confidence=float(row["confidence"] or 1.0),
        detected_at=row["detected_at"],
        updated_at=row["updated_at"],
        payload=json.loads(row["payload_json"] or "{}"),
    )
