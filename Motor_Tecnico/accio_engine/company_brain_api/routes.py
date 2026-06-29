"""API v1 — Company Brain (tenant scope)."""

from __future__ import annotations

from functools import wraps

from flask import request

from Motor_Tecnico.accio_engine.company_brain_api.composition import company_brain_use_cases, reset_company_brain_use_cases
from Motor_Tecnico.accio_engine.company_brain_api.dto import brain_to_response
from Motor_Tecnico.accio_engine.company_brain_api.http_helpers import error_response, success
from Motor_Tecnico.accio_engine.company_brain_api.request_context import tenant_context
from Motor_Tecnico.accio_engine.company_brain_application.errors import ApplicationError


def reset_use_cases_cache() -> None:
    reset_company_brain_use_cases()


def _handle_application_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ApplicationError as exc:
            return error_response(exc)

    return wrapped


def register_company_brain_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/company-brain"

    @app.get(base)
    @auth_decorator
    @_handle_application_errors
    def api_get_company_brain(tenant_id: str):
        ctx = tenant_context(tenant_id)
        brain = company_brain_use_cases().get(ctx)
        return success(brain_to_response(brain))

    @app.patch(base)
    @auth_decorator
    @_handle_application_errors
    def api_patch_company_brain(tenant_id: str):
        ctx = tenant_context(tenant_id)
        body = request.get_json(silent=True) or {}
        profile_patch = body.get("profile", body)
        brain = company_brain_use_cases().update(ctx, profile_patch)
        return success(brain_to_response(brain))
