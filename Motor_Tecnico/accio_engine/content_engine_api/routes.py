"""Content Engine API."""

from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.content_engine_api.composition import content_engine_use_cases, tenant_context
from Motor_Tecnico.accio_engine.content_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _piece_response(piece: ContentPiece) -> dict:
    return piece.to_api_dict()


def register_content_engine_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/content"

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
    def api_list_content(tenant_id: str):
        from flask import request

        status = request.args.get("status")
        campaign_id = request.args.get("campaign_id")
        brand_id = request.args.get("brand_id")
        limit = min(int(request.args.get("limit", 50)), 100)
        rows = content_engine_use_cases().list_content(
            tenant_context(tenant_id),
            status=status,
            campaign_id=campaign_id,
            brand_id=brand_id,
            limit=limit,
        )
        return _success([_piece_response(r) for r in rows])

    @app.get(f"{base}/<content_id>")
    @auth_decorator
    @_handle
    def api_get_content(tenant_id: str, content_id: str):
        row = content_engine_use_cases().get_content(tenant_context(tenant_id), content_id)
        return _success(_piece_response(row))

    @app.get(f"{base}/<content_id>/explain")
    @auth_decorator
    @_handle
    def api_get_content_explain(tenant_id: str, content_id: str):
        data = content_engine_use_cases().get_explain(tenant_context(tenant_id), content_id)
        return _success(data)

    @app.patch(f"{base}/<content_id>")
    @auth_decorator
    @_handle
    def api_patch_content(tenant_id: str, content_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        row = content_engine_use_cases().patch_content(tenant_context(tenant_id), content_id, body)
        return _success(_piece_response(row))

    @app.post(f"{base}/from-campaign/<campaign_id>")
    @auth_decorator
    @_handle
    def api_create_content_from_campaign(tenant_id: str, campaign_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        enrich = bool(body.get("enrich", False))
        row = content_engine_use_cases().from_campaign(
            tenant_context(tenant_id),
            campaign_id,
            enrich=enrich,
        )
        return _success(_piece_response(row), status=201)

    @app.post(f"{base}/<content_id>/enrich")
    @auth_decorator
    @_handle
    def api_enrich_content(tenant_id: str, content_id: str):
        row = content_engine_use_cases().enrich_content(tenant_context(tenant_id), content_id)
        return _success(_piece_response(row))

    @app.post(f"{base}/<content_id>/approve")
    @auth_decorator
    @_handle
    def api_approve_content(tenant_id: str, content_id: str):
        row = content_engine_use_cases().approve_content(tenant_context(tenant_id), content_id)
        return _success(_piece_response(row))
