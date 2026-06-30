from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_api.composition import (
    build_recommendation_service,
    decision_engine_use_cases,
)
from Motor_Tecnico.accio_engine.decision_engine_application.use_cases import CreateRecommendationFromCandidate
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.application_adapters import DecisionEngineRbacAdapter
from Motor_Tecnico.accio_engine.marketing_brain_api.composition import marketing_brain_use_cases
from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
from Motor_Tecnico.accio_engine.opportunity_application.context import TenantContext
from Motor_Tecnico.accio_engine.opportunity_application.use_cases import (
    DetectAndPromoteOpportunities,
    DetectOpportunities,
    DismissOpportunity,
    GetOpportunity,
    ListOpportunities,
    PromoteOpportunity,
    RunMarketingPipeline,
)
from Motor_Tecnico.accio_engine.opportunity_domain.promotion_service import OpportunityPromotionService
from Motor_Tecnico.accio_engine.opportunity_domain.service import OpportunityDetectionService
from Motor_Tecnico.accio_engine.opportunity_infrastructure.application_adapters import OpportunityRbacAdapter
from Motor_Tecnico.accio_engine.opportunity_infrastructure.intelligence_bridge import OpportunityIntelligenceBridge
from Motor_Tecnico.accio_engine.opportunity_infrastructure.knowledge_reader import CompositeOpportunityKnowledgeReader
from Motor_Tecnico.accio_engine.opportunity_infrastructure.sqlite_repository import SqliteOpportunityRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_opportunity_repository() -> SqliteOpportunityRepository:
    ensure_schema()
    return SqliteOpportunityRepository()


def build_opportunity_detector() -> OpportunityDetectionService:
    return OpportunityDetectionService(
        build_opportunity_repository(),
        CompositeOpportunityKnowledgeReader(),
    )


def build_opportunity_promotion() -> OpportunityPromotionService:
    return OpportunityPromotionService(build_opportunity_repository())


def build_opportunity_intelligence() -> OpportunityIntelligenceBridge:
    return OpportunityIntelligenceBridge(CompositeOpportunityKnowledgeReader())


class OpportunityUseCases:
    def __init__(self) -> None:
        detector = build_opportunity_detector()
        promotion = build_opportunity_promotion()
        intelligence = build_opportunity_intelligence()
        recommendations = build_recommendation_service()
        auth = OpportunityRbacAdapter()
        memory = get_memory_domain_service()
        de_auth = DecisionEngineRbacAdapter()
        create_recommendation = CreateRecommendationFromCandidate(
            recommendations,
            de_auth,
            memory,
        )
        self.detect_opportunities = DetectOpportunities(detector, auth, memory)
        self.list_opportunities = ListOpportunities(detector, auth)
        self.get_opportunity = GetOpportunity(detector, auth)
        self.promote_opportunity = PromoteOpportunity(
            promotion,
            create_recommendation,
            intelligence,
            recommendations,
            auth,
            memory,
        )
        self.dismiss_opportunity = DismissOpportunity(promotion, auth, memory)
        self.detect_and_promote = DetectAndPromoteOpportunities(
            self.detect_opportunities,
            self.promote_opportunity,
            auth,
        )
        de = decision_engine_use_cases()
        mb = marketing_brain_use_cases()
        self.run_pipeline = RunMarketingPipeline(
            self.detect_and_promote,
            de.generate_daily_roadmap,
            mb.enrich_daily_roadmap,
            auth,
        )


_USE_CASES: OpportunityUseCases | None = None


def reset_opportunity_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def opportunity_use_cases() -> OpportunityUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = OpportunityUseCases()
    return _USE_CASES


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
