from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.opportunity_api.composition import opportunity_use_cases, reset_opportunity_use_cases, tenant_context
from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity


def reset_use_cases_cache() -> None:
    reset_opportunity_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _opportunity_response(row: Opportunity) -> dict:
    return row.to_api_dict()


def _actor_id() -> str:
    from flask import session

    return str(session.get("user_id") or "system")


def register_opportunity_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/opportunities"

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
    def api_list_opportunities(tenant_id: str):
        from flask import request

        brand_id = request.args.get("app_id") or request.args.get("brand_id")
        status = request.args.get("status")
        limit = min(int(request.args.get("limit", 50)), 200)
        rows = opportunity_use_cases().list_opportunities(
            tenant_context(tenant_id),
            brand_id=brand_id,
            status=status,
            limit=limit,
        )
        return _success([_opportunity_response(r) for r in rows])

    @app.post(f"{base}/detect")
    @auth_decorator
    @_handle
    def api_detect_opportunities(tenant_id: str):
        result = opportunity_use_cases().detect_opportunities(
            tenant_context(tenant_id),
            actor_id=_actor_id(),
        )
        return _success(
            {
                "created_count": result.created_count,
                "updated_count": result.updated_count,
                "opportunities": [_opportunity_response(o) for o in result.opportunities],
            },
            status=201 if result.created_count else 200,
        )

    @app.post(f"{base}/detect-and-promote")
    @auth_decorator
    @_handle
    def api_detect_and_promote_opportunities(tenant_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        priority = body.get("priority", "high")
        limit = min(int(body.get("limit", 10)), 20)
        result = opportunity_use_cases().detect_and_promote(
            tenant_context(tenant_id),
            priority=str(priority) if priority else None,
            limit=limit,
            actor_id=_actor_id(),
        )
        return _success(
            {
                "created_count": result.detection.created_count,
                "updated_count": result.detection.updated_count,
                "promoted_count": result.promoted_count,
                "skipped_count": result.skipped_count,
                "promoted": [
                    {
                        "opportunity": _opportunity_response(p.opportunity),
                        "recommendation": p.recommendation.to_api_dict(),
                    }
                    for p in result.promoted
                ],
            },
            status=201 if result.promoted_count else 200,
        )

    @app.post(f"{base}/run-pipeline")
    @auth_decorator
    @_handle
    def api_run_marketing_pipeline(tenant_id: str):
        from flask import request

        from Motor_Tecnico.accio_engine.decision_engine_api.routes import _roadmap_response

        body = request.get_json(silent=True) or {}
        priority = body.get("priority", "high")
        limit = min(int(body.get("limit", 10)), 20)
        enrich = bool(body.get("enrich", True))
        result = opportunity_use_cases().run_pipeline(
            tenant_context(tenant_id),
            priority=str(priority) if priority else None,
            limit=limit,
            enrich=enrich,
            actor_id=_actor_id(),
        )
        payload = {
            "promoted_count": result.promote.promoted_count,
            "skipped_count": result.promote.skipped_count,
            "created_count": result.promote.detection.created_count,
            "roadmap": _roadmap_response(result.roadmap),
            "llm_skipped": result.llm_skipped,
        }
        if result.enrichment is not None:
            payload["enrichment"] = {
                "enriched_count": result.enrichment.enriched_count,
                "skipped_count": result.enrichment.skipped_count,
                "failed_count": result.enrichment.failed_count,
                "persisted": result.enrichment.persisted,
            }
        status = 201 if result.promote.promoted_count or result.roadmap.created else 200
        return _success(payload, status=status)

    @app.get(f"{base}/<opportunity_id>")
    @auth_decorator
    @_handle
    def api_get_opportunity(tenant_id: str, opportunity_id: str):
        row = opportunity_use_cases().get_opportunity(tenant_context(tenant_id), opportunity_id)
        return _success(_opportunity_response(row))

    @app.post(f"{base}/<opportunity_id>/promote")
    @auth_decorator
    @_handle
    def api_promote_opportunity(tenant_id: str, opportunity_id: str):
        result = opportunity_use_cases().promote_opportunity(
            tenant_context(tenant_id),
            opportunity_id,
            actor_id=_actor_id(),
        )
        return _success(
            {
                "opportunity": _opportunity_response(result.opportunity),
                "recommendation": result.recommendation.to_api_dict(),
            },
            status=201,
        )

    @app.post(f"{base}/<opportunity_id>/dismiss")
    @auth_decorator
    @_handle
    def api_dismiss_opportunity(tenant_id: str, opportunity_id: str):
        row = opportunity_use_cases().dismiss_opportunity(
            tenant_context(tenant_id),
            opportunity_id,
            actor_id=_actor_id(),
        )
        return _success(_opportunity_response(row))
