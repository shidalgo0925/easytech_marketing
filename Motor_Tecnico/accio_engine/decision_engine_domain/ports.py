from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap, Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot


class KnowledgeReader(Protocol):
    def read(self, tenant_id: str) -> KnowledgeSnapshot: ...


class RecommendationRepository(Protocol):
    def save(self, recommendation: Recommendation) -> None: ...

    def get(self, tenant_id: str, recommendation_id: str) -> Recommendation | None: ...

    def list_recommendations(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        owner_role: str | None = None,
        roadmap_id: str | None = None,
        limit: int = 50,
    ) -> list[Recommendation]: ...


class DailyRoadmapRepository(Protocol):
    def save(self, roadmap: DailyRoadmap) -> None: ...

    def get_by_date(self, tenant_id: str, company_id: str, roadmap_date: str) -> DailyRoadmap | None: ...

    def get_by_id(self, tenant_id: str, roadmap_id: str) -> DailyRoadmap | None: ...
