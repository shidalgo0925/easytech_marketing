"""OpportunityScorer — puntuación 0–100 a partir de reglas + contexto."""

from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.model import (
    OPPORTUNITY_SCORER_VERSION,
    OpportunityScoreResult,
    resolve_opportunity_priority,
)
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity, OpportunityCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot

_RULE_PRIORITY = {"high": 0.9, "medium": 0.6, "low": 0.35}
_SIGNAL_IMPACT = {
    "lead_followup_gap": 0.9,
    "brand_inactive": 0.78,
    "campaign_stalled": 0.72,
}
_WEIGHTS = {
    "rule_priority": 0.20,
    "age": 0.15,
    "commercial_impact": 0.18,
    "leads_affected": 0.15,
    "campaigns_related": 0.10,
    "recent_activity": 0.12,
    "brain_alignment": 0.10,
}


def _parse_iso(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _brand_key(brand: Brand) -> str:
    return brand.legacy_app_id or brand.brand_id


def _days_since(iso_timestamp: str, reference_at: datetime) -> int | None:
    dt = _parse_iso(iso_timestamp)
    if dt is None:
        return None
    ref = reference_at.astimezone(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0, (ref.date() - dt.astimezone(timezone.utc).date()).days)


class OpportunityScorer:
    def score_candidate(
        self,
        candidate: OpportunityCandidate,
        snapshot: OpportunitySnapshot,
        *,
        reference_at: datetime | None = None,
    ) -> OpportunityScoreResult:
        ref = reference_at or datetime.now(timezone.utc)
        return self._score_internal(
            signal_type=candidate.signal_type,
            brand_id=candidate.brand_id,
            rule_priority=candidate.priority,
            payload=candidate.payload or {},
            confidence=candidate.confidence,
            snapshot=snapshot,
            reference_at=ref,
        )

    def score_opportunity(
        self,
        opportunity: Opportunity,
        snapshot: OpportunitySnapshot,
        *,
        reference_at: datetime | None = None,
    ) -> OpportunityScoreResult:
        ref = reference_at or datetime.now(timezone.utc)
        return self._score_internal(
            signal_type=opportunity.signal_type,
            brand_id=opportunity.brand_id,
            rule_priority=opportunity.priority,
            payload=opportunity.payload or {},
            confidence=opportunity.confidence,
            snapshot=snapshot,
            reference_at=ref,
        )

    def _score_internal(
        self,
        *,
        signal_type: str,
        brand_id: str,
        rule_priority: str,
        payload: dict,
        confidence: float,
        snapshot: OpportunitySnapshot,
        reference_at: datetime,
    ) -> OpportunityScoreResult:
        factors: dict[str, float] = {}
        reasoning: list[str] = []

        factors["rule_priority"] = _RULE_PRIORITY.get(rule_priority, 0.5)
        reasoning.append(f"Prioridad de regla «{rule_priority}» → factor {factors['rule_priority']:.0%}")

        gap_days = payload.get("gap_days") or payload.get("stale_days") or payload.get("days_since_last_published")
        try:
            gap = int(gap_days) if gap_days is not None else 7
        except (TypeError, ValueError):
            gap = 7
        factors["age"] = min(gap / 30.0, 1.0)
        reasoning.append(f"Antigüedad de la señal ({gap} días) → factor {factors['age']:.0%}")

        factors["commercial_impact"] = _SIGNAL_IMPACT.get(signal_type, 0.55)
        reasoning.append(f"Impacto comercial de «{signal_type}» → factor {factors['commercial_impact']:.0%}")

        leads = snapshot.leads_by_brand.get(brand_id, ())
        lead_count = len(leads)
        factors["leads_affected"] = min(lead_count / 10.0, 1.0) if lead_count else 0.2
        if lead_count:
            reasoning.append(f"{lead_count} lead(s) afectados en la marca → factor {factors['leads_affected']:.0%}")

        campaigns = snapshot.campaigns_by_brand.get(brand_id, ())
        stalled = sum(1 for c in campaigns if (c.status or "").lower() in {"draft", "paused", "stopped", "inactive"})
        factors["campaigns_related"] = min(stalled / 3.0, 1.0) if stalled else 0.15
        if stalled:
            reasoning.append(f"{stalled} campaña(s) relacionada(s) estancada(s)")

        pubs = snapshot.publications_by_brand.get(brand_id, ())
        last_pub = None
        for p in pubs:
            ts = p.published_at or p.scheduled_at or p.created_at
            if ts and (last_pub is None or ts > last_pub):
                last_pub = ts
        inactive_days = _days_since(last_pub, reference_at) if last_pub else 30
        factors["recent_activity"] = min((inactive_days or 30) / 30.0, 1.0)
        reasoning.append(f"Inactividad reciente estimada ({inactive_days or '—'} días sin publicación fuerte)")

        profile = snapshot.company_brain.profile if snapshot.company_brain else {}
        products = [str(p).lower() for p in (profile.get("productos_servicios") or [])]
        slug = (payload.get("product_slug") or brand_id or "").lower()
        aligned = any(slug in p or p in slug for p in products) if products and slug else False
        factors["brain_alignment"] = 0.85 if aligned else 0.35
        if aligned:
            reasoning.append(f"Producto «{slug}» alineado con Company Brain")
        else:
            reasoning.append(f"Producto «{slug}» con alineación parcial al portafolio declarado")

        weighted = sum(factors[k] * _WEIGHTS[k] for k in _WEIGHTS)
        score = round(min(max(weighted * 100, 0), 100), 2)
        priority = resolve_opportunity_priority(rule_priority, score)
        conf = min(max(confidence * 0.4 + (score / 100) * 0.6, 0.1), 1.0)

        return OpportunityScoreResult(
            score=score,
            confidence=round(conf, 3),
            priority=priority,
            reasoning=tuple(reasoning),
            factors=factors,
            algorithm_version=OPPORTUNITY_SCORER_VERSION,
        )
