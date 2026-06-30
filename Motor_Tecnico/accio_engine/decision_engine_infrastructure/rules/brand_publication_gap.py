"""Rule: brand_publication_gap — recommend publish when brand inactive too long."""

from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot
from Motor_Tecnico.accio_engine.publication_domain.model import Publication

RULE_ID = "brand_publication_gap"
DEFAULT_THRESHOLD_DAYS = 7

_PENDING_STATUSES = frozenset({"pending", "scheduled", "draft"})


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def days_since_activity(iso_timestamp: str, reference_at: datetime) -> int | None:
    dt = _parse_iso(iso_timestamp)
    if dt is None:
        return None
    ref = _as_utc(reference_at)
    return (ref.date() - _as_utc(dt).date()).days


def _brand_key(brand: Brand) -> str:
    return brand.legacy_app_id or brand.brand_id


def _last_published_at(publications: tuple[Publication, ...]) -> str | None:
    published = [
        p
        for p in publications
        if p.status.lower() == "published" and (p.published_at or p.scheduled_at)
    ]
    if not published:
        return None
    return max(p.published_at or p.scheduled_at for p in published)


def _pending_publications(publications: tuple[Publication, ...]) -> list[Publication]:
    pending = [p for p in publications if p.status.lower() in _PENDING_STATUSES]
    return sorted(pending, key=lambda p: p.scheduled_at or p.created_at or p.publication_id)


def _priority_for_gap(days: int) -> str:
    if days >= DEFAULT_THRESHOLD_DAYS:
        return "high"
    return "medium"


def evaluate_brand_publication_gap(
    snapshot: KnowledgeSnapshot,
    *,
    reference_at: datetime,
    threshold_days: int = DEFAULT_THRESHOLD_DAYS,
) -> list[RecommendationCandidate]:
    candidates: list[RecommendationCandidate] = []

    for brand in snapshot.brands:
        brand_id = _brand_key(brand)
        publications = snapshot.publications_by_brand.get(brand_id, ())
        pending = _pending_publications(publications)
        if not pending:
            continue

        last_published = _last_published_at(publications)
        if last_published:
            gap_days = days_since_activity(last_published, reference_at)
            if gap_days is None or gap_days < threshold_days:
                continue
        else:
            gap_days = threshold_days

        target = pending[0]
        priority = _priority_for_gap(gap_days)
        reason = f"Sin publicaciones en {gap_days} días"
        description = (
            f"Hay {len(pending)} publicación(es) pendiente(s). "
            f"Siguiente sugerida: {target.publication_id} ({target.channel})."
        )
        content_type = str((target.payload or {}).get("content_type") or "")

        candidates.append(
            RecommendationCandidate(
                brand_id=brand_id,
                title=f"Publicar {brand.name}",
                description=description,
                action="publish",
                reason=reason,
                priority=priority,
                owner_role="marketing",
                source=f"rule:{RULE_ID}",
                confidence=1.0,
                justification_refs={
                    "brand_id": brand_id,
                    "publication_id": target.publication_id,
                    "legacy_queue_id": target.legacy_queue_id,
                    "days_since_last_published": gap_days,
                    "threshold_days": threshold_days,
                    "pending_count": len(pending),
                    "content_type": content_type,
                },
            )
        )

    return candidates
