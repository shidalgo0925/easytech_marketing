from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.decision_engine_api.routes import _error, _success
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import tenant_today_iso
from Motor_Tecnico.accio_engine.marketing_brain_api.composition import marketing_brain_use_cases, reset_marketing_brain_use_cases
from Motor_Tecnico.accio_engine.decision_engine_api.composition import tenant_context


def reset_use_cases_cache() -> None:
    reset_marketing_brain_use_cases()


def _actor_id() -> str:
    from flask import session

    return str(session.get("user_id") or "system")


def register_marketing_brain_api(app, auth_decorator) -> None:
    rec_base = "/api/v1/tenants/<tenant_id>/recommendations/<recommendation_id>/enrich"
    roadmap_base = "/api/v1/tenants/<tenant_id>/roadmaps"

    def _handle(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                return view(*args, **kwargs)
            except ApplicationError as exc:
                return _error(exc)
            except PermissionError as exc:
                return _error(ApplicationError("forbidden", str(exc), 403))

        return wrapped

    @app.post(rec_base)
    @auth_decorator
    @_handle
    def api_enrich_recommendation(tenant_id: str, recommendation_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        persist = bool(body.get("persist", False))
        rec, enrichment = marketing_brain_use_cases().enrich_recommendation(
            tenant_context(tenant_id),
            recommendation_id,
            persist=persist,
            actor_id=_actor_id(),
        )
        return _success(
            {
                "recommendation": rec.to_api_dict(),
                "enrichment": enrichment.to_dict(),
                "persisted": persist,
            }
        )

    @app.post(f"{roadmap_base}/<roadmap_date>/enrich")
    @auth_decorator
    @_handle
    def api_enrich_daily_roadmap(tenant_id: str, roadmap_date: str):
        from flask import request

        if roadmap_date == "today":
            roadmap_date = tenant_today_iso()
        body = request.get_json(silent=True) or {}
        persist = bool(body.get("persist", False))
        skip_enriched = bool(body.get("skip_enriched", True))
        limit = min(int(body.get("limit", 20)), 50)
        result = marketing_brain_use_cases().enrich_daily_roadmap(
            tenant_context(tenant_id),
            roadmap_date,
            persist=persist,
            skip_enriched=skip_enriched,
            limit=limit,
            actor_id=_actor_id(),
        )
        return _success(result.to_dict())
