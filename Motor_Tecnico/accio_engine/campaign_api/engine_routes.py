"""Campaign Engine API — tenant-scoped REST v1."""

from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.campaign_api.composition import campaign_engine_use_cases, tenant_context
from Motor_Tecnico.accio_engine.campaign_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _campaign_response(campaign: Campaign) -> dict:
    return campaign.to_api_dict()


def register_campaign_engine_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/campaigns"

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
    def api_list_engine_campaigns(tenant_id: str):
        from flask import request

        status = request.args.get("status")
        brand_id = request.args.get("brand_id")
        limit = min(int(request.args.get("limit", 50)), 100)
        rows = campaign_engine_use_cases().list_campaigns(
            tenant_context(tenant_id),
            status=status,
            brand_id=brand_id,
            limit=limit,
        )
        return _success([_campaign_response(c) for c in rows])

    @app.get(f"{base}/<campaign_id>")
    @auth_decorator
    @_handle
    def api_get_engine_campaign(tenant_id: str, campaign_id: str):
        row = campaign_engine_use_cases().get_campaign(tenant_context(tenant_id), campaign_id)
        return _success(_campaign_response(row))

    @app.get(f"{base}/<campaign_id>/explain")
    @auth_decorator
    @_handle
    def api_get_campaign_explain(tenant_id: str, campaign_id: str):
        data = campaign_engine_use_cases().get_explain(tenant_context(tenant_id), campaign_id)
        return _success(data)

    @app.patch(f"{base}/<campaign_id>")
    @auth_decorator
    @_handle
    def api_patch_campaign(tenant_id: str, campaign_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        row = campaign_engine_use_cases().patch_campaign(
            tenant_context(tenant_id),
            campaign_id,
            body,
        )
        return _success(_campaign_response(row))

    @app.post(f"{base}/from-recommendation/<recommendation_id>")
    @auth_decorator
    @_handle
    def api_create_campaign_from_recommendation(tenant_id: str, recommendation_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        enrich = bool(body.get("enrich", False))
        row = campaign_engine_use_cases().from_recommendation(
            tenant_context(tenant_id),
            recommendation_id,
            enrich=enrich,
        )
        return _success(_campaign_response(row), status=201)

    @app.post(f"{base}/<campaign_id>/enrich")
    @auth_decorator
    @_handle
    def api_enrich_campaign(tenant_id: str, campaign_id: str):
        row = campaign_engine_use_cases().enrich_campaign(tenant_context(tenant_id), campaign_id)
        return _success(_campaign_response(row))

    @app.post(f"{base}/<campaign_id>/approve")
    @auth_decorator
    @_handle
    def api_approve_campaign(tenant_id: str, campaign_id: str):
        row = campaign_engine_use_cases().approve_campaign(tenant_context(tenant_id), campaign_id)
        return _success(_campaign_response(row))

    @app.post(f"{base}/<campaign_id>/archive")
    @auth_decorator
    @_handle
    def api_archive_campaign(tenant_id: str, campaign_id: str):
        row = campaign_engine_use_cases().archive_campaign(tenant_context(tenant_id), campaign_id)
        return _success(_campaign_response(row))
