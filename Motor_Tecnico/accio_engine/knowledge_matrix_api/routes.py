from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.knowledge_matrix_api.composition import (
    knowledge_matrix_use_cases,
    reset_knowledge_matrix_use_cases,
    tenant_context,
)
from Motor_Tecnico.accio_engine.knowledge_matrix_application.errors import ApplicationError


def reset_use_cases_cache() -> None:
    reset_knowledge_matrix_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def register_knowledge_matrix_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/knowledge-matrix"

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
    def api_get_knowledge_matrix(tenant_id: str):
        matrix = knowledge_matrix_use_cases().get_matrix(tenant_context(tenant_id))
        return _success(matrix.to_dict())

    @app.post(f"{base}/classify")
    @auth_decorator
    @_handle
    def api_classify_knowledge_matrix(tenant_id: str):
        from flask import request

        body = request.get_json(silent=True) or {}
        text = str(body.get("text") or "")
        brand_id = body.get("brand_id") or body.get("app_id")
        result = knowledge_matrix_use_cases().classify(
            tenant_context(tenant_id),
            text=text,
            brand_id=str(brand_id) if brand_id else None,
        )
        return _success(result.to_dict())
