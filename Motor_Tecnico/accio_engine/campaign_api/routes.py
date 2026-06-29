from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.campaign_api.composition import campaign_use_cases, reset_campaign_use_cases, tenant_app_context
from Motor_Tecnico.accio_engine.campaign_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign


def reset_use_cases_cache() -> None:
    reset_campaign_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _campaign_response(campaign: Campaign) -> dict:
    return campaign.to_api_dict()


def register_campaign_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/apps/<app_id>/campaigns"

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
    def api_list_campaigns(tenant_id: str, app_id: str):
        ctx = tenant_app_context(tenant_id, app_id)
        rows = campaign_use_cases().list_campaigns(ctx)
        return _success([_campaign_response(c) for c in rows])

    @app.get(f"{base}/<campaign_id>")
    @auth_decorator
    @_handle
    def api_get_campaign(tenant_id: str, app_id: str, campaign_id: str):
        ctx = tenant_app_context(tenant_id, app_id)
        row = campaign_use_cases().get_campaign(ctx, campaign_id)
        return _success(_campaign_response(row))
