from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.rules.brand_publication_gap import (
    _last_published_at,
    _pending_publications,
    days_since_activity,
)
from Motor_Tecnico.accio_engine.opportunity_domain.model import OpportunityCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot

RULE_ID = "brand_inactive"
DEFAULT_THRESHOLD_DAYS = 14


def _brand_key(brand: Brand) -> str:
    return brand.legacy_app_id or brand.brand_id


def _product_slug(brand: Brand) -> str:
    return (brand.slug or brand.legacy_app_id or brand.brand_id).lower()


def _landing_for(brand: Brand) -> str:
    slug = _product_slug(brand)
    if slug in ("default", "easytech"):
        return "https://n8n.etsrv.site/guia/"
    return f"https://n8n.etsrv.site/{slug}/"


def evaluate_brand_inactive(
    snapshot: OpportunitySnapshot,
    *,
    reference_at: datetime,
    threshold_days: int = DEFAULT_THRESHOLD_DAYS,
) -> list[OpportunityCandidate]:
    candidates: list[OpportunityCandidate] = []
    for brand in snapshot.brands:
        brand_id = _brand_key(brand)
        publications = snapshot.publications_by_brand.get(brand_id, ())
        pending = _pending_publications(publications)
        if pending:
            continue
        last_pub = _last_published_at(publications)
        if last_pub:
            days = days_since_activity(last_pub, reference_at)
            if days is None or days < threshold_days:
                continue
            gap_days = days
        else:
            gap_days = threshold_days

        signal_key = f"{RULE_ID}:{brand_id}"
        candidates.append(
            OpportunityCandidate(
                signal_key=signal_key,
                signal_type=RULE_ID,
                brand_id=brand_id,
                title=f"Marca inactiva — {brand.name}",
                description=(
                    f"Sin publicaciones pendientes ni actividad reciente en {brand.name} "
                    f"({gap_days} días sin señal fuerte)."
                ),
                sector="B2B",
                need="Visibilidad y recordatorio de marca en canales digitales",
                product_slug=_product_slug(brand),
                channel="linkedin",
                landing_url=_landing_for(brand),
                priority="high" if gap_days >= threshold_days * 2 else "medium",
                source=RULE_ID,
                payload={"gap_days": gap_days, "last_published_at": last_pub},
            )
        )
    return candidates
