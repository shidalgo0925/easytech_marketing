from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.product_api.composition import product_use_cases, reset_product_use_cases, tenant_app_context
from Motor_Tecnico.accio_engine.product_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.product_domain.model import Product


def reset_use_cases_cache() -> None:
    reset_product_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _product_response(product: Product) -> dict:
    return product.to_api_dict()


def register_product_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/apps/<app_id>/products"

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
    def api_list_products(tenant_id: str, app_id: str):
        from flask import request

        active_only = request.args.get("active_only", "true").lower() != "false"
        ctx = tenant_app_context(tenant_id, app_id)
        rows = product_use_cases().list_products(ctx, active_only=active_only)
        return _success([_product_response(p) for p in rows])

    @app.get(f"{base}/<product_id>")
    @auth_decorator
    @_handle
    def api_get_product(tenant_id: str, app_id: str, product_id: str):
        ctx = tenant_app_context(tenant_id, app_id)
        row = product_use_cases().get_product(ctx, product_id)
        return _success(_product_response(row))
