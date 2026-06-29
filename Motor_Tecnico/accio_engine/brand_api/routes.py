from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.brand_api.composition import brand_use_cases, reset_brand_use_cases
from Motor_Tecnico.accio_engine.brand_api.request_context import tenant_context
from Motor_Tecnico.accio_engine.brand_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.brand_domain.model import Brand


def reset_use_cases_cache() -> None:
    reset_brand_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _brand_response(brand: Brand) -> dict:
    return brand.to_api_dict()


def register_brand_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/brands"

    def _handle(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                return view(*args, **kwargs)
            except ApplicationError as exc:
                return _error(exc)

        return wrapped

    @app.get(base)
    @auth_decorator
    @_handle
    def api_list_brands(tenant_id: str):
        ctx = tenant_context(tenant_id)
        rows = brand_use_cases().list_brands(ctx)
        return _success([_brand_response(b) for b in rows])

    @app.get(f"{base}/<brand_id>")
    @auth_decorator
    @_handle
    def api_get_brand(tenant_id: str, brand_id: str):
        ctx = tenant_context(tenant_id)
        row = brand_use_cases().get_brand(ctx, brand_id)
        return _success(_brand_response(row))
