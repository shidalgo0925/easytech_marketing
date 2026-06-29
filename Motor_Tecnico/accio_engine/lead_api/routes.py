from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.lead_api.composition import lead_use_cases, reset_lead_use_cases, tenant_context
from Motor_Tecnico.accio_engine.lead_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.lead_domain.model import Lead


def reset_use_cases_cache() -> None:
    reset_lead_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _lead_response(lead: Lead) -> dict:
    return lead.to_api_dict()


def register_lead_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/leads"

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
    def api_list_leads(tenant_id: str):
        from flask import request

        brand_id = request.args.get("app_id") or request.args.get("brand_id")
        limit = min(int(request.args.get("limit", 50)), 200)
        ctx = tenant_context(tenant_id)
        rows = lead_use_cases().list_leads(ctx, brand_id=brand_id, limit=limit)
        return _success([_lead_response(lead) for lead in rows])

    @app.get(f"{base}/<lead_id>")
    @auth_decorator
    @_handle
    def api_get_lead(tenant_id: str, lead_id: str):
        ctx = tenant_context(tenant_id)
        row = lead_use_cases().get_lead(ctx, lead_id)
        return _success(_lead_response(row))
