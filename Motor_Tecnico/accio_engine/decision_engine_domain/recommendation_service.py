from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.decision_engine_domain.errors import (
    InvalidRecommendationTransition,
    RecommendationNotFound,
    RejectionReasonRequired,
    SnoozeUntilRequired,
)
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation, RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.ports import RecommendationRepository
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.recommendation_mapper import candidate_to_recommendation

_APPROVABLE_STATUSES = frozenset({"pending_approval", "snoozed"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecommendationDomainService:
    def __init__(self, repository: RecommendationRepository) -> None:
        self._repo = repository

    def create_from_candidate(
        self,
        tenant_id: str,
        candidate: RecommendationCandidate,
        *,
        created_by: str = "system",
        roadmap_id: str | None = None,
    ) -> Recommendation:
        recommendation = candidate_to_recommendation(
            tenant_id,
            candidate,
            created_by=created_by,
            roadmap_id=roadmap_id,
        )
        self._repo.save(recommendation)
        return recommendation

    def get_recommendation(self, tenant_id: str, recommendation_id: str) -> Recommendation:
        row = self._repo.get(tenant_id, recommendation_id)
        if row is None:
            raise RecommendationNotFound(recommendation_id)
        return row

    def list_recommendations(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        owner_role: str | None = None,
        roadmap_id: str | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        return self._repo.list_recommendations(
            tenant_id,
            brand_id=brand_id,
            status=status,
            owner_role=owner_role,
            roadmap_id=roadmap_id,
            limit=limit,
        )

    def approve_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        *,
        actor_id: str,
    ) -> Recommendation:
        rec = self._require_approvable(tenant_id, recommendation_id, action="aprobar")
        updated = replace(
            rec,
            status="approved",
            approved_by=actor_id,
            rejected_by=None,
            updated_at=_utc_now(),
        )
        self._repo.update(updated)
        return updated

    def reject_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        *,
        actor_id: str,
        reason: str,
    ) -> Recommendation:
        if not (reason or "").strip():
            raise RejectionReasonRequired()
        rec = self._require_approvable(tenant_id, recommendation_id, action="rechazar")
        result = dict(rec.result or {})
        result["rejection_reason"] = reason.strip()
        updated = replace(
            rec,
            status="rejected",
            rejected_by=actor_id,
            approved_by=None,
            result=result,
            updated_at=_utc_now(),
        )
        self._repo.update(updated)
        return updated

    def snooze_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        *,
        actor_id: str,
        until: str,
    ) -> Recommendation:
        if not (until or "").strip():
            raise SnoozeUntilRequired()
        rec = self._require_approvable(tenant_id, recommendation_id, action="posponer")
        result = dict(rec.result or {})
        result["snoozed_by"] = actor_id
        result["snoozed_until"] = until.strip()
        updated = replace(
            rec,
            status="snoozed",
            due_at=until.strip(),
            result=result,
            updated_at=_utc_now(),
        )
        self._repo.update(updated)
        return updated

    def apply_enrichment(
        self,
        tenant_id: str,
        recommendation_id: str,
        enrichment: object,
    ) -> Recommendation:
        """M11 — persiste reason/description/confidence enriquecidos por IA."""
        rec = self.get_recommendation(tenant_id, recommendation_id)
        refs = dict(rec.justification_refs or {})
        refs["ai_enrichment"] = {
            "model": getattr(enrichment, "model", ""),
            "at": _utc_now(),
            "narrative": getattr(enrichment, "narrative", ""),
            "original_reason": rec.reason,
            "original_description": rec.description,
            "original_confidence": rec.confidence,
        }
        updated = replace(
            rec,
            reason=getattr(enrichment, "reason", rec.reason),
            description=getattr(enrichment, "description", rec.description),
            confidence=float(getattr(enrichment, "confidence", rec.confidence)),
            justification_refs=refs,
            updated_at=_utc_now(),
        )
        self._repo.update(updated)
        return updated

    def _require_approvable(self, tenant_id: str, recommendation_id: str, *, action: str) -> Recommendation:
        rec = self.get_recommendation(tenant_id, recommendation_id)
        if rec.status not in _APPROVABLE_STATUSES:
            raise InvalidRecommendationTransition(recommendation_id, rec.status, action)
        return rec
