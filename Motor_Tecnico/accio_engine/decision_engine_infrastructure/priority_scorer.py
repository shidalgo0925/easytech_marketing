"""M10.2 — deterministic priority scoring for recommendation candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate, priority_from_score
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot
from Motor_Tecnico.accio_engine.lead_domain.model import Lead

MAX_INACTIVITY_DAYS = 30
RECENT_LEAD_DAYS = 14

_UNCONTACTED_STATUSES = frozenset({"new", "open", "pending", "sin_contacto", "uncontacted"})


@dataclass(frozen=True)
class PriorityWeights:
    inactivity: float = 0.40
    product_alignment: float = 0.25
    leads_follow_up: float = 0.20
    editorial_balance: float = 0.15


DEFAULT_WEIGHTS = PriorityWeights()

_BRAND_PRODUCT_ALIASES: dict[str, frozenset[str]] = {
    "en1": frozenset({"en1", "easynodeone", "easy node one"}),
    "odoo-fe": frozenset({"odoo", "facturación", "facturacion", "dgi", "fe"}),
    "eposone": frozenset({"eposone", "pos", "punto de venta"}),
    "eclassone": frozenset({"eclassone", "académica", "academica", "matrícula"}),
    "ethesisone": frozenset({"ethesisone", "tesis"}),
    "epayroll": frozenset({"epayroll", "planilla"}),
    "consultoria": frozenset({"consultoría", "consultoria", "ti estratégica"}),
    "desarrollo": frozenset({"desarrollo", "software a medida"}),
}


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


def _inactivity_score(candidate: RecommendationCandidate) -> float:
    gap = candidate.justification_refs.get("days_since_last_published")
    if gap is None:
        return 0.5
    try:
        days = int(gap)
    except (TypeError, ValueError):
        return 0.5
    return min(max(days, 0) / MAX_INACTIVITY_DAYS, 1.0)


def _brand_tokens(brand: Brand) -> set[str]:
    tokens = {brand.slug.lower(), brand.name.lower(), brand.legacy_app_id.lower()}
    aliases = _BRAND_PRODUCT_ALIASES.get(brand.legacy_app_id, frozenset())
    tokens.update(a.lower() for a in aliases)
    return {t for t in tokens if t}


def _product_alignment_score(brand: Brand | None, profile: dict) -> float:
    products = profile.get("productos_servicios") or []
    if not brand or not products:
        return 0.5
    tokens = _brand_tokens(brand)
    for index, product in enumerate(products):
        product_lower = str(product).lower()
        if any(token in product_lower for token in tokens if len(token) > 2):
            rank_bonus = 1.0 - (index / max(len(products), 1)) * 0.5
            return round(min(max(rank_bonus, 0.3), 1.0), 4)
    return 0.2


def _recent_uncontacted_leads(
    leads: tuple[Lead, ...],
    *,
    reference_at: datetime,
) -> int:
    ref = _as_utc(reference_at)
    count = 0
    for lead in leads:
        if lead.status.lower() not in _UNCONTACTED_STATUSES:
            continue
        created = _parse_iso(lead.created_at)
        if created is None:
            count += 1
            continue
        days = (ref.date() - _as_utc(created).date()).days
        if days <= RECENT_LEAD_DAYS:
            count += 1
    return count


def _leads_follow_up_score(leads: tuple[Lead, ...], *, reference_at: datetime) -> float:
    count = _recent_uncontacted_leads(leads, reference_at=reference_at)
    if count <= 0:
        return 0.0
    if count >= 3:
        return 1.0
    if count == 2:
        return 0.8
    return 0.6


def _editorial_balance_score(candidate: RecommendationCandidate) -> float:
    content_type = str(candidate.justification_refs.get("content_type") or "").strip().lower()
    if not content_type:
        return 0.5
    if content_type == "venta":
        return 0.65
    if content_type in {"valor", "educativo", "autoridad", "caso"}:
        return 1.0
    return 0.75


class PriorityScorer:
    """Weighted scorer — output is deterministic for the same snapshot + candidates."""

    def __init__(self, weights: PriorityWeights | None = None) -> None:
        self._weights = weights or DEFAULT_WEIGHTS

    def score(
        self,
        candidate: RecommendationCandidate,
        snapshot: KnowledgeSnapshot,
        *,
        reference_at: datetime,
    ) -> RecommendationCandidate:
        brand = snapshot.brand_by_id(candidate.brand_id)
        profile = snapshot.brain_profile()
        leads = snapshot.leads_by_brand.get(candidate.brand_id, ())

        factors = {
            "inactivity": round(_inactivity_score(candidate), 4),
            "product_alignment": round(_product_alignment_score(brand, profile), 4),
            "leads_follow_up": round(_leads_follow_up_score(leads, reference_at=reference_at), 4),
            "editorial_balance": round(_editorial_balance_score(candidate), 4),
        }
        w = self._weights
        total = (
            factors["inactivity"] * w.inactivity
            + factors["product_alignment"] * w.product_alignment
            + factors["leads_follow_up"] * w.leads_follow_up
            + factors["editorial_balance"] * w.editorial_balance
        )
        total = round(min(max(total, 0.0), 1.0), 4)
        refs = dict(candidate.justification_refs)
        refs["priority_factors"] = factors
        refs["priority_weights"] = {
            "inactivity": w.inactivity,
            "product_alignment": w.product_alignment,
            "leads_follow_up": w.leads_follow_up,
            "editorial_balance": w.editorial_balance,
        }
        return replace(
            candidate,
            priority_score=total,
            priority=priority_from_score(total),
            justification_refs=refs,
        )

    def score_and_sort(
        self,
        candidates: list[RecommendationCandidate],
        snapshot: KnowledgeSnapshot,
        *,
        reference_at: datetime,
    ) -> list[RecommendationCandidate]:
        scored = [self.score(c, snapshot, reference_at=reference_at) for c in candidates]
        return sorted(scored, key=lambda c: (-c.priority_score, c.brand_id))
