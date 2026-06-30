"""Marketing Intelligence Layer — application use cases."""

from __future__ import annotations

from dataclasses import replace

from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.decision_engine_domain.errors import DecisionEngineError
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.explainability import explain_from_recommendation, similarity_key
from Motor_Tecnico.accio_engine.opportunity_domain.errors import OpportunityEngineError
from Motor_Tecnico.accio_engine.opportunity_domain.errors import OpportunityEngineError
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.service import OpportunityDetectionService
from Motor_Tecnico.accio_engine.opportunity_infrastructure.intelligence_bridge import OpportunityIntelligenceBridge
from Motor_Tecnico.accio_engine.opportunity_infrastructure.mapper import candidate_to_opportunity


class GetRecommendationExplain:
    def __init__(self, recommendations: RecommendationDomainService, authorization: AuthorizationPort) -> None:
        self._recommendations = recommendations
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, recommendation_id: str) -> dict:
        self._authorization.require_permission(ctx, "read")
        try:
            rec = self._recommendations.get_recommendation(ctx.tenant_id, recommendation_id)
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        explain = explain_from_recommendation(rec)
        if explain is None:
            raise ApplicationError("explain_not_found", "No hay explicación técnica para esta recomendación", 404)
        return {
            "recommendation_id": recommendation_id,
            "explain": explain,
            "composed": rec.composed,
            "ai_enrichment": (rec.justification_refs or {}).get("ai_enrichment"),
        }


class RecomposeRecommendation:
    def __init__(
        self,
        recommendations: RecommendationDomainService,
        intelligence: OpportunityIntelligenceBridge,
        detector: OpportunityDetectionService,
        authorization: AuthorizationPort,
    ) -> None:
        self._recommendations = recommendations
        self._intelligence = intelligence
        self._detector = detector
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, recommendation_id: str, *, actor_id: str = "system") -> Recommendation:
        self._authorization.require_permission(ctx, "write")
        try:
            rec = self._recommendations.get_recommendation(ctx.tenant_id, recommendation_id)
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        opp_id = (rec.justification_refs or {}).get("opportunity_id")
        if not opp_id:
            raise ApplicationError("opportunity_missing", "La recomendación no está ligada a una oportunidad", 400)
        try:
            opp = self._detector.get_opportunity(ctx.tenant_id, str(opp_id))
        except OpportunityEngineError as exc:
            from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError as OppApplicationError

            raise OppApplicationError.from_domain(exc) from exc
        candidate, composed, score, explain = self._intelligence.compose_promotion(ctx.tenant_id, opp)
        updated = replace(
            rec,
            title=candidate.title,
            description=candidate.description,
            action=candidate.action,
            reason=candidate.reason,
            priority=candidate.priority,
            priority_score=candidate.priority_score,
            confidence=candidate.confidence,
            justification_refs=candidate.justification_refs,
            expected_roi=composed.expected_impact,
            explain=explain,
            composed=composed.to_dict(),
            updated_at=rec.updated_at,
        )
        updated = self._intelligence.attach_to_recommendation(
            updated,
            composed=composed,
            explain=explain,
            score=score,
        )
        return self._recommendations.save_recommendation(updated)


class RescoreOpportunity:
    def __init__(
        self,
        detector: OpportunityDetectionService,
        intelligence: OpportunityIntelligenceBridge,
        authorization: AuthorizationPort,
    ) -> None:
        self._detector = detector
        self._intelligence = intelligence
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, opportunity_id: str) -> Opportunity:
        self._authorization.require_permission(ctx, "write")
        try:
            opp = self._detector.get_opportunity(ctx.tenant_id, opportunity_id)
        except OpportunityEngineError as exc:
            from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError as OppApplicationError

            raise OppApplicationError.from_domain(exc) from exc
        score = self._intelligence.score_opportunity(ctx.tenant_id, opp)
        return self._detector.rescore(ctx.tenant_id, opportunity_id, score)


class ListSimilarRecommendations:
    def __init__(self, recommendations: RecommendationDomainService, authorization: AuthorizationPort) -> None:
        self._recommendations = recommendations
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, recommendation_id: str, *, limit: int = 5) -> list[Recommendation]:
        self._authorization.require_permission(ctx, "read")
        try:
            base = self._recommendations.get_recommendation(ctx.tenant_id, recommendation_id)
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        key = similarity_key(base)
        rows = self._recommendations.list_recommendations(ctx.tenant_id, limit=100)
        similar = [
            r
            for r in rows
            if r.recommendation_id != recommendation_id and similarity_key(r) == key
        ]
        return similar[: max(1, min(limit, 20))]
