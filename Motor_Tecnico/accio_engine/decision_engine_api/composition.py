from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.use_cases import (
    BuildRecommendationCandidates,
    CreateRecommendationFromCandidate,
    GenerateDailyRoadmap,
    GetDailyRoadmap,
    GetRecommendation,
    ListRecommendations,
)
from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.service import RoadmapBuilderService
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.application_adapters import DecisionEngineRbacAdapter
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.daily_roadmap_sqlite_repository import (
    SqliteDailyRoadmapRepository,
)
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.knowledge_reader import CompositeKnowledgeReader
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.sqlite_repository import SqliteRecommendationRepository
from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_recommendation_service() -> RecommendationDomainService:
    ensure_schema()
    return RecommendationDomainService(SqliteRecommendationRepository())


def build_daily_roadmap_service(builder: RoadmapBuilderService) -> DailyRoadmapDomainService:
    ensure_schema()
    return DailyRoadmapDomainService(
        SqliteDailyRoadmapRepository(),
        build_recommendation_service(),
        builder,
    )


class DecisionEngineUseCases:
    def __init__(self) -> None:
        builder = RoadmapBuilderService(CompositeKnowledgeReader())
        recommendations = build_recommendation_service()
        roadmaps = build_daily_roadmap_service(builder)
        auth = DecisionEngineRbacAdapter()
        memory = get_memory_domain_service()
        self.build_candidates = BuildRecommendationCandidates(builder)
        self.create_from_candidate = CreateRecommendationFromCandidate(recommendations, auth, memory)
        self.list_recommendations = ListRecommendations(recommendations, auth)
        self.get_recommendation = GetRecommendation(recommendations, auth)
        self.generate_daily_roadmap = GenerateDailyRoadmap(roadmaps, auth, memory)
        self.get_daily_roadmap = GetDailyRoadmap(roadmaps, auth)


_USE_CASES: DecisionEngineUseCases | None = None
_BUILDER: RoadmapBuilderService | None = None


def reset_decision_engine_use_cases() -> None:
    global _USE_CASES, _BUILDER
    _USE_CASES = None
    _BUILDER = None


def decision_engine_use_cases() -> DecisionEngineUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = DecisionEngineUseCases()
    return _USE_CASES


def reset_decision_engine() -> None:
    reset_decision_engine_use_cases()
    from Motor_Tecnico.accio_engine.brand_infrastructure.facade import reset_brand_service
    from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import reset_company_brain_service
    from Motor_Tecnico.accio_engine.lead_infrastructure.facade import reset_lead_service
    from Motor_Tecnico.accio_engine.publication_infrastructure.facade import reset_publication_service
    from Motor_Tecnico.accio_engine.memory_api.composition import reset_memory_use_cases

    reset_brand_service()
    reset_publication_service()
    reset_company_brain_service()
    reset_lead_service()
    reset_memory_use_cases()


def roadmap_builder() -> RoadmapBuilderService:
    global _BUILDER
    if _BUILDER is None:
        _BUILDER = RoadmapBuilderService(CompositeKnowledgeReader())
    return _BUILDER


def build_candidates_use_case() -> BuildRecommendationCandidates:
    return BuildRecommendationCandidates(roadmap_builder())


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
