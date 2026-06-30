"""Bridge Opportunity → Recommendation con Marketing Intelligence Layer."""

from __future__ import annotations

from dataclasses import replace

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation, RecommendationCandidate
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.explainability import build_explain
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.model import (
    ComposedRecommendation,
    OpportunityScoreResult,
)
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.opportunity_scorer import OpportunityScorer
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.recommendation_composer import RecommendationComposer
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.ports import OpportunityKnowledgeReader


class OpportunityIntelligenceBridge:
    def __init__(
        self,
        knowledge_reader: OpportunityKnowledgeReader,
        scorer: OpportunityScorer | None = None,
        composer: RecommendationComposer | None = None,
    ) -> None:
        self._reader = knowledge_reader
        self._scorer = scorer or OpportunityScorer()
        self._composer = composer or RecommendationComposer()

    def score_opportunity(self, tenant_id: str, opportunity: Opportunity) -> OpportunityScoreResult:
        snapshot = self._reader.read(tenant_id)
        return self._scorer.score_opportunity(opportunity, snapshot)

    def compose_promotion(
        self,
        tenant_id: str,
        opportunity: Opportunity,
        *,
        score: OpportunityScoreResult | None = None,
    ) -> tuple[RecommendationCandidate, ComposedRecommendation, OpportunityScoreResult, dict]:
        snapshot = self._reader.read(tenant_id)
        score_result = score or self._scorer.score_opportunity(opportunity, snapshot)
        composed = self._composer.compose(opportunity, score_result)
        candidate = self._composer.to_candidate(opportunity, composed, score_result)
        context_keys = (
            "company_brain",
            "brands",
            "publications",
            "campaigns",
            "leads",
            "knowledge_matrix",
        )
        explain = build_explain(
            opportunity=opportunity,
            score=score_result,
            composed=composed,
            context_keys=context_keys,
            data_used={
                "brand_id": opportunity.brand_id,
                "product_slug": opportunity.product_slug,
                "payload": dict(opportunity.payload or {}),
                "score": score_result.to_dict(),
            },
        ).to_dict()
        return candidate, composed, score_result, explain

    def attach_to_recommendation(
        self,
        recommendation: Recommendation,
        *,
        composed: ComposedRecommendation,
        explain: dict,
        score: OpportunityScoreResult,
    ) -> Recommendation:
        return replace(
            recommendation,
            explain=explain,
            composed=composed.to_dict(),
            expected_roi=composed.expected_impact,
            priority=score.priority,
            priority_score=score.score / 100.0,
            confidence=score.confidence,
        )
