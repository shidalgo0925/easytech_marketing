from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.media_asset_api.composition import (
    media_asset_use_cases,
    reset_media_asset_use_cases,
    tenant_context,
)
from Motor_Tecnico.accio_engine.media_asset_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset


def reset_use_cases_cache() -> None:
    reset_media_asset_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _asset_response(asset: MediaAsset) -> dict:
    return asset.to_api_dict()


def register_media_asset_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/assets"

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
    def api_list_assets(tenant_id: str):
        from flask import request

        asset_type = request.args.get("type") or request.args.get("asset_type")
        ctx = tenant_context(tenant_id)
        rows = media_asset_use_cases().list_assets(ctx, asset_type=asset_type)
        return _success([_asset_response(a) for a in rows])

    @app.get(f"{base}/<asset_id>")
    @auth_decorator
    @_handle
    def api_get_asset(tenant_id: str, asset_id: str):
        ctx = tenant_context(tenant_id)
        row = media_asset_use_cases().get_asset(ctx, asset_id)
        return _success(_asset_response(row))
