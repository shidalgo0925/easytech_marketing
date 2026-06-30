from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment


class MarketingBrainLLM(Protocol):
    def enrich_recommendation(self, recommendation: Recommendation) -> RecommendationEnrichment: ...
