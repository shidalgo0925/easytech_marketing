from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.opportunity_domain.model import OpportunityCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot

RULE_ID = "lead_followup_gap"
OPEN_STATUSES = frozenset({"new", "open", "contacted"})
DEFAULT_GAP_DAYS = 3


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _days_since(iso_timestamp: str, reference_at: datetime) -> int | None:
    dt = _parse_iso(iso_timestamp)
    if dt is None:
        return None
    ref = reference_at.astimezone(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (ref.date() - dt.astimezone(timezone.utc).date()).days


def evaluate_lead_followup_gap(
    snapshot: OpportunitySnapshot,
    *,
    reference_at: datetime,
    gap_days: int = DEFAULT_GAP_DAYS,
) -> list[OpportunityCandidate]:
    candidates: list[OpportunityCandidate] = []
    for brand_id, leads in snapshot.leads_by_brand.items():
        for lead in leads:
            status = (lead.status or "").lower()
            if status not in OPEN_STATUSES:
                continue
            days = _days_since(lead.created_at or lead.updated_at, reference_at)
            if days is None or days < gap_days:
                continue
            signal_key = f"{RULE_ID}:{brand_id}:{lead.lead_id}"
            product = (lead.payload or {}).get("product") or brand_id
            candidates.append(
                OpportunityCandidate(
                    signal_key=signal_key,
                    signal_type=RULE_ID,
                    brand_id=brand_id,
                    title=f"Lead sin seguimiento — {lead.lead_id}",
                    description=f"Lead en estado «{status}» hace {days} días sin cierre.",
                    sector="B2B",
                    need="Seguimiento comercial o nutrición de lead",
                    product_slug=str(product).lower(),
                    channel=lead.channel or "web",
                    landing_url=lead.landing_url or "https://n8n.etsrv.site/guia/",
                    priority="high" if days >= gap_days * 2 else "medium",
                    source=RULE_ID,
                    payload={
                        "lead_id": lead.lead_id,
                        "lead_status": status,
                        "gap_days": days,
                    },
                )
            )
    return candidates
