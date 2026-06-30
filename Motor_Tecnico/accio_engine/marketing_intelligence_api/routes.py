"""Marketing Intelligence API — explainability v2."""

from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.decision_engine_api.composition import (
    build_opportunity_detector_for_intelligence,
    build_recommendation_service,
    tenant_context,
)
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.application_adapters import DecisionEngineRbacAdapter
from Motor_Tecnico.accio_engine.marketing_intelligence_application.use_cases import (
    GetRecommendationExplain,
    ListSimilarRecommendations,
    RecomposeRecommendation,
    RescoreOpportunity,
)
from Motor_Tecnico.accio_engine.opportunity_infrastructure.intelligence_bridge import OpportunityIntelligenceBridge
from Motor_Tecnico.accio_engine.opportunity_infrastructure.knowledge_reader import CompositeOpportunityKnowledgeReader


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _rec_response(row: Recommendation) -> dict:
    return row.to_api_dict()


class _IntelligenceUseCases:
    def __init__(self) -> None:
        recommendations = build_recommendation_service()
        detector = build_opportunity_detector_for_intelligence()
        intelligence = OpportunityIntelligenceBridge(CompositeOpportunityKnowledgeReader())
        auth = DecisionEngineRbacAdapter()
        self.get_explain = GetRecommendationExplain(recommendations, auth)
        self.recompose = RecomposeRecommendation(recommendations, intelligence, detector, auth)
        self.rescore_opportunity = RescoreOpportunity(detector, intelligence, auth)
        self.similar = ListSimilarRecommendations(recommendations, auth)


_USE_CASES: _IntelligenceUseCases | None = None


def intelligence_use_cases() -> _IntelligenceUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = _IntelligenceUseCases()
    return _USE_CASES


def reset_intelligence_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def register_marketing_intelligence_api(app, auth_decorator) -> None:
    rec_base = "/api/v1/tenants/<tenant_id>/recommendations"
    opp_base = "/api/v1/tenants/<tenant_id>/opportunities"

    def _handle(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                return view(*args, **kwargs)
            except ApplicationError as exc:
                return _error(exc)
            except PermissionError as exc:
                return _error(ApplicationError("forbidden", str(exc), 403))
            except Exception as exc:
                from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError as OppApplicationError

                if isinstance(exc, OppApplicationError):
                    return _error(ApplicationError(exc.code, exc.message, exc.http_status))
                raise

        return wrapped

    @app.get(f"{rec_base}/<recommendation_id>/explain")
    @auth_decorator
    @_handle
    def api_get_recommendation_explain(tenant_id: str, recommendation_id: str):
        data = intelligence_use_cases().get_explain(tenant_context(tenant_id), recommendation_id)
        return _success(data)

    @app.post(f"{rec_base}/<recommendation_id>/recompose")
    @auth_decorator
    @_handle
    def api_recompose_recommendation(tenant_id: str, recommendation_id: str):
        row = intelligence_use_cases().recompose(tenant_context(tenant_id), recommendation_id)
        return _success(_rec_response(row))

    @app.get(f"{rec_base}/<recommendation_id>/similar")
    @auth_decorator
    @_handle
    def api_similar_recommendations(tenant_id: str, recommendation_id: str):
        from flask import request

        limit = min(int(request.args.get("limit", 5)), 20)
        rows = intelligence_use_cases().similar(
            tenant_context(tenant_id),
            recommendation_id,
            limit=limit,
        )
        return _success([_rec_response(r) for r in rows])

    @app.post(f"{opp_base}/<opportunity_id>/rescore")
    @auth_decorator
    @_handle
    def api_rescore_opportunity(tenant_id: str, opportunity_id: str):
        from Motor_Tecnico.accio_engine.opportunity_api.routes import _opportunity_response

        row = intelligence_use_cases().rescore_opportunity(tenant_context(tenant_id), opportunity_id)
        return _success(_opportunity_response(row))
