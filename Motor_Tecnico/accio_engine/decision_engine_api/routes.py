from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.decision_engine_api.composition import (
    decision_engine_use_cases,
    reset_decision_engine_use_cases,
    tenant_context,
)
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapBundle
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import tenant_today_iso


def reset_use_cases_cache() -> None:
    reset_decision_engine_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _recommendation_response(row: Recommendation) -> dict:
    return row.to_api_dict()


def _roadmap_response(bundle: DailyRoadmapBundle) -> dict:
    return bundle.roadmap.to_api_dict(recommendations=bundle.recommendations)


def _actor_id() -> str:
    from flask import session

    return str(session.get("user_id") or "system")


def register_decision_engine_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/recommendations"
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

    @app.get(base)
    @auth_decorator
    @_handle
    def api_list_recommendations(tenant_id: str):
        from flask import request

        brand_id = request.args.get("app_id") or request.args.get("brand_id")
        status = request.args.get("status")
        owner_role = request.args.get("owner_role")
        limit = min(int(request.args.get("limit", 50)), 200)
        ctx = tenant_context(tenant_id)
        rows = decision_engine_use_cases().list_recommendations(
            ctx,
            brand_id=brand_id,
            status=status,
            owner_role=owner_role,
            limit=limit,
        )
        return _success([_recommendation_response(r) for r in rows])

    @app.get(f"{base}/<recommendation_id>")
    @auth_decorator
    @_handle
    def api_get_recommendation(tenant_id: str, recommendation_id: str):
        ctx = tenant_context(tenant_id)
        row = decision_engine_use_cases().get_recommendation(ctx, recommendation_id)
        return _success(_recommendation_response(row))

    @app.post(f"{roadmap_base}/<roadmap_date>/generate")
    @auth_decorator
    @_handle
    def api_generate_daily_roadmap(tenant_id: str, roadmap_date: str):
        if roadmap_date == "today":
            roadmap_date = tenant_today_iso()
        ctx = tenant_context(tenant_id)
        bundle = decision_engine_use_cases().generate_daily_roadmap(ctx, roadmap_date)
        status = 201 if bundle.created else 200
        return _success(_roadmap_response(bundle), status=status)

    @app.get(f"{roadmap_base}/today")
    @auth_decorator
    @_handle
    def api_get_today_roadmap(tenant_id: str):
        ctx = tenant_context(tenant_id)
        bundle = decision_engine_use_cases().get_daily_roadmap(ctx, tenant_today_iso())
        return _success(_roadmap_response(bundle))

    @app.get(f"{roadmap_base}/<roadmap_date>")
    @auth_decorator
    @_handle
    def api_get_daily_roadmap(tenant_id: str, roadmap_date: str):
        if roadmap_date == "today":
            roadmap_date = tenant_today_iso()
        ctx = tenant_context(tenant_id)
        bundle = decision_engine_use_cases().get_daily_roadmap(ctx, roadmap_date)
        return _success(_roadmap_response(bundle))

    @app.post(f"{base}/<recommendation_id>/approve")
    @auth_decorator
    @_handle
    def api_approve_recommendation(tenant_id: str, recommendation_id: str):
        ctx = tenant_context(tenant_id)
        row = decision_engine_use_cases().approve_recommendation(
            ctx,
            recommendation_id,
            actor_id=_actor_id(),
        )
        return _success(_recommendation_response(row))

    @app.post(f"{base}/<recommendation_id>/reject")
    @auth_decorator
    @_handle
    def api_reject_recommendation(tenant_id: str, recommendation_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        reason = str(body.get("reason") or "")
        ctx = tenant_context(tenant_id)
        row = decision_engine_use_cases().reject_recommendation(
            ctx,
            recommendation_id,
            actor_id=_actor_id(),
            reason=reason,
        )
        return _success(_recommendation_response(row))

    @app.post(f"{base}/<recommendation_id>/snooze")
    @auth_decorator
    @_handle
    def api_snooze_recommendation(tenant_id: str, recommendation_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        until = str(body.get("until") or "")
        ctx = tenant_context(tenant_id)
        row = decision_engine_use_cases().snooze_recommendation(
            ctx,
            recommendation_id,
            actor_id=_actor_id(),
            until=until,
        )
        return _success(_recommendation_response(row))
