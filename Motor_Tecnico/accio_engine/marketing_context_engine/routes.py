"""API Marketing Context Engine."""

from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder


def register_marketing_context_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/marketing-context"

    def _success(data, *, status: int = 200):
        from flask import jsonify

        return jsonify({"ok": True, "data": data}), status

    def _handle(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError

            try:
                return view(*args, **kwargs)
            except ApplicationError as exc:
                from flask import jsonify

                return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status

        return wrapped

    @app.get(base)
    @auth_decorator
    @_handle
    def api_get_marketing_context(tenant_id: str):
        from flask import request

        app_id = request.args.get("app_id")
        purpose = request.args.get("purpose", "full")
        builder = get_marketing_context_builder()
        if purpose == "llm":
            data = builder.build_for_llm(tenant_id, app_id=app_id)
        else:
            data = builder.build(tenant_id, app_id=app_id)
        return _success(data)
