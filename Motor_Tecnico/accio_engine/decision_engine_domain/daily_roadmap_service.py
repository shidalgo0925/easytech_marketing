from __future__ import annotations

from dataclasses import dataclass

from Motor_Tecnico.accio_engine.decision_engine_domain.errors import DailyRoadmapNotFound
from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap, Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.ports import DailyRoadmapRepository, RecommendationRepository
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.service import RoadmapBuilderService
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import (
    _utc_now,
    build_roadmap_summary,
    new_roadmap_id,
    reference_at_for_date,
)


@dataclass(frozen=True)
class DailyRoadmapBundle:
    roadmap: DailyRoadmap
    recommendations: list[Recommendation]
    created: bool = False


class DailyRoadmapDomainService:
    """M10.4 — idempotent daily roadmap generation."""

    def __init__(
        self,
        roadmap_repository: DailyRoadmapRepository,
        recommendation_service: RecommendationDomainService,
        builder: RoadmapBuilderService,
    ) -> None:
        self._roadmaps = roadmap_repository
        self._recommendations = recommendation_service
        self._builder = builder

    def get_daily_roadmap(
        self,
        tenant_id: str,
        roadmap_date: str,
        *,
        company_id: str | None = None,
    ) -> DailyRoadmapBundle:
        company = company_id or tenant_id
        roadmap = self._roadmaps.get_by_date(tenant_id, company, roadmap_date)
        if roadmap is None:
            raise DailyRoadmapNotFound(roadmap_date)
        recs = self._recommendations.list_recommendations(
            tenant_id,
            roadmap_id=roadmap.roadmap_id,
            limit=200,
        )
        return DailyRoadmapBundle(roadmap=roadmap, recommendations=recs)

    def generate_daily_roadmap(
        self,
        tenant_id: str,
        roadmap_date: str,
        *,
        company_id: str | None = None,
        created_by: str = "system",
    ) -> DailyRoadmapBundle:
        company = company_id or tenant_id
        existing = self._roadmaps.get_by_date(tenant_id, company, roadmap_date)
        if existing is not None:
            recs = self._recommendations.list_recommendations(
                tenant_id,
                roadmap_id=existing.roadmap_id,
                limit=200,
            )
            return DailyRoadmapBundle(roadmap=existing, recommendations=recs, created=False)

        roadmap_id = new_roadmap_id(roadmap_date)
        reference_at = reference_at_for_date(roadmap_date)
        candidates = self._builder.build_candidates(tenant_id, reference_at=reference_at)

        persisted: list[Recommendation] = []
        for candidate in candidates:
            persisted.append(
                self._recommendations.create_from_candidate(
                    tenant_id,
                    candidate,
                    created_by=created_by,
                    roadmap_id=roadmap_id,
                )
            )

        roadmap = DailyRoadmap(
            tenant_id=tenant_id,
            roadmap_id=roadmap_id,
            company_id=company,
            roadmap_date=roadmap_date,
            generated_at=_utc_now(),
            summary=build_roadmap_summary(persisted),
        )
        self._roadmaps.save(roadmap)
        return DailyRoadmapBundle(roadmap=roadmap, recommendations=persisted, created=True)

    def apply_ai_enrichment_summary(
        self,
        tenant_id: str,
        roadmap_id: str,
        ai_summary: dict,
    ) -> DailyRoadmap:
        from dataclasses import replace

        roadmap = self._roadmaps.get_by_id(tenant_id, roadmap_id)
        if roadmap is None:
            raise DailyRoadmapNotFound(roadmap_id)
        summary = dict(roadmap.summary or {})
        summary["ai_enrichment"] = ai_summary
        updated = replace(roadmap, summary=summary)
        self._roadmaps.update(updated)
        return updated
