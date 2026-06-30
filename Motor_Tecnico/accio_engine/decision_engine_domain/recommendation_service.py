from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_domain.errors import RecommendationNotFound
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation, RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.ports import RecommendationRepository
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.recommendation_mapper import candidate_to_recommendation


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
