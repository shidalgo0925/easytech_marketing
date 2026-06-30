from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.opportunity_domain.model import OpportunityCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot

RULE_ID = "campaign_stalled"
STALLED_STATUSES = frozenset({"draft", "paused", "stopped", "inactive"})
DEFAULT_STALE_DAYS = 14


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


def evaluate_campaign_stalled(
    snapshot: OpportunitySnapshot,
    *,
    reference_at: datetime,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> list[OpportunityCandidate]:
    candidates: list[OpportunityCandidate] = []
    for brand in snapshot.brands:
        brand_id = brand.legacy_app_id or brand.brand_id
        for campaign in snapshot.campaigns_by_brand.get(brand_id, ()):
            status = (campaign.status or "").lower()
            if status not in STALLED_STATUSES:
                continue
            anchor = campaign.updated_at or campaign.created_at or campaign.start_at
            if campaign.payload:
                anchor = campaign.payload.get("updated_at") or anchor
            days = _days_since(anchor, reference_at)
            if days is None or days < stale_days:
                continue
            signal_key = f"{RULE_ID}:{brand_id}:{campaign.campaign_id}"
            product = (campaign.product_ref or brand.slug or brand_id).lower()
            candidates.append(
                OpportunityCandidate(
                    signal_key=signal_key,
                    signal_type=RULE_ID,
                    brand_id=brand_id,
                    title=f"Campaña detenida — {campaign.name}",
                    description=(
                        f"La campaña «{campaign.name}» lleva {days} días en estado «{status}» "
                        f"sin avance."
                    ),
                    sector="B2B",
                    need="Reactivar o cerrar campaña para no perder momentum comercial",
                    product_slug=product,
                    channel=campaign.channel or "linkedin",
                    landing_url="https://n8n.etsrv.site/guia/",
                    priority="medium",
                    source=RULE_ID,
                    payload={
                        "campaign_id": campaign.campaign_id,
                        "campaign_status": status,
                        "stale_days": days,
                    },
                )
            )
    return candidates
