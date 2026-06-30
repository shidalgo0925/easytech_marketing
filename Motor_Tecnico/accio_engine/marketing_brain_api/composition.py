from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_api.composition import (
    build_daily_roadmap_service,
    build_recommendation_service,
    roadmap_builder,
)
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.application_adapters import DecisionEngineRbacAdapter
from Motor_Tecnico.accio_engine.marketing_brain_application.use_cases import EnrichDailyRoadmap, EnrichRecommendation
from Motor_Tecnico.accio_engine.marketing_brain_domain.service import MarketingBrainDomainService
from Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client import AiProviderMarketingBrainLLM
from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service


class MarketingBrainUseCases:
    def __init__(self) -> None:
        recommendations = build_recommendation_service()
        brain = MarketingBrainDomainService(AiProviderMarketingBrainLLM(), recommendations)
        roadmaps = build_daily_roadmap_service(roadmap_builder())
        auth = DecisionEngineRbacAdapter()
        memory = get_memory_domain_service()
        self.enrich_recommendation = EnrichRecommendation(brain, auth, memory)
        self.enrich_daily_roadmap = EnrichDailyRoadmap(brain, roadmaps, recommendations, auth, memory)


_USE_CASES: MarketingBrainUseCases | None = None


def reset_marketing_brain_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def marketing_brain_use_cases() -> MarketingBrainUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = MarketingBrainUseCases()
    return _USE_CASES
