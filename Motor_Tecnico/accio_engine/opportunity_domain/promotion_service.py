from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.opportunity_domain.errors import InvalidOpportunityTransition, OpportunityNotFound
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.ports import OpportunityRepository
from Motor_Tecnico.accio_engine.opportunity_infrastructure.recommendation_bridge import opportunity_to_candidate

_PROMOTABLE_STATUSES = frozenset({"detected"})
_DISMISSABLE_STATUSES = frozenset({"detected", "classified"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PromotionResult:
    opportunity: Opportunity
    recommendation: Recommendation


class OpportunityPromotionService:
    """F2 — convierte oportunidades en recomendaciones del Decision Engine."""

    def __init__(self, repository: OpportunityRepository) -> None:
        self._repo = repository

    def to_candidate(self, tenant_id: str, opportunity_id: str) -> tuple[Opportunity, object]:
        opp = self._require_status(tenant_id, opportunity_id, allowed=_PROMOTABLE_STATUSES, action="promover")
        return opp, opportunity_to_candidate(opp)

    def mark_promoted(
        self,
        tenant_id: str,
        opportunity_id: str,
        recommendation: Recommendation,
    ) -> Opportunity:
        opp = self._repo.get(tenant_id, opportunity_id)
        if opp is None:
            raise OpportunityNotFound(opportunity_id)
        payload = dict(opp.payload or {})
        payload["recommendation_id"] = recommendation.recommendation_id
        updated = replace(
            opp,
            status="classified",
            payload=payload,
            updated_at=_utc_now(),
        )
        self._repo.update(updated)
        return updated

    def dismiss(self, tenant_id: str, opportunity_id: str) -> Opportunity:
        opp = self._require_status(tenant_id, opportunity_id, allowed=_DISMISSABLE_STATUSES, action="descartar")
        updated = replace(opp, status="dismissed", updated_at=_utc_now())
        self._repo.update(updated)
        return updated

    def _require_status(
        self,
        tenant_id: str,
        opportunity_id: str,
        *,
        allowed: frozenset[str],
        action: str,
    ) -> Opportunity:
        opp = self._repo.get(tenant_id, opportunity_id)
        if opp is None:
            raise OpportunityNotFound(opportunity_id)
        if opp.status not in allowed:
            raise InvalidOpportunityTransition(opportunity_id, opp.status, action)
        return opp
