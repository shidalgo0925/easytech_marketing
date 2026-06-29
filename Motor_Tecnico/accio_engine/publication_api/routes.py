from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.publication_api.composition import publication_use_cases, reset_publication_use_cases, tenant_app_context
from Motor_Tecnico.accio_engine.publication_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.publication_domain.model import Publication


def reset_use_cases_cache() -> None:
    reset_publication_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _publication_response(pub: Publication) -> dict:
    return pub.to_api_dict()


def register_publication_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/apps/<app_id>/publications"

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
    def api_list_publications(tenant_id: str, app_id: str):
        from flask import request

        status = request.args.get("status")
        ctx = tenant_app_context(tenant_id, app_id)
        rows = publication_use_cases().list_publications(ctx, status=status)
        return _success([_publication_response(p) for p in rows])

    @app.get(f"{base}/<publication_id>")
    @auth_decorator
    @_handle
    def api_get_publication(tenant_id: str, app_id: str, publication_id: str):
        ctx = tenant_app_context(tenant_id, app_id)
        row = publication_use_cases().get_publication(ctx, publication_id)
        return _success(_publication_response(row))
