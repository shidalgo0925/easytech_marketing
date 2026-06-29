"""Rutas API v1 — MarketingPlan + slice (context, planner)."""

from __future__ import annotations

from functools import wraps

from flask import request

from Motor_Tecnico.accio_engine.marketing_context_builder import build_marketing_context
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import (
    GetActiveMarketingPlanQuery,
    GetMarketingPlanQuery,
)
from Motor_Tecnico.accio_engine.marketing_planner import generate_proposals
from Motor_Tecnico.accio_engine.marketing_plan_api.composition import marketing_plan_use_cases
from Motor_Tecnico.accio_engine.marketing_plan_api.dto import (
    activate_input_from_json,
    create_input_from_json,
    plan_to_response,
)
from Motor_Tecnico.accio_engine.marketing_plan_api.http_helpers import (
    error_response,
    http_status_for_application_error,
    success,
)
from Motor_Tecnico.accio_engine.marketing_plan_api.request_context import application_context


def _use_cases():
    return marketing_plan_use_cases()


def reset_use_cases_cache() -> None:
    """Solo tests — fuerza nuevo composition root."""
    from Motor_Tecnico.accio_engine.marketing_plan_api.composition import reset_marketing_plan_use_cases

    reset_marketing_plan_use_cases()


def _handle_application_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ApplicationError as exc:
            return error_response(exc, http_status=http_status_for_application_error(exc))

    return wrapped


def register_marketing_plan_api(app, auth_decorator):
    base = "/api/v1/tenants/<tenant_id>/apps/<app_id>"

    @app.post(f"{base}/marketing-plans")
    @auth_decorator
    @_handle_application_errors
    def api_create_marketing_plan(tenant_id: str, app_id: str):
        body = request.get_json(silent=True) or {}
        ctx = application_context(tenant_id, app_id)
        result = _use_cases().create(ctx, create_input_from_json(body))
        return success(plan_to_response(result.plan), status=201)

    @app.get(f"{base}/marketing-plans/active")
    @auth_decorator
    @_handle_application_errors
    def api_get_active_marketing_plan(tenant_id: str, app_id: str):
        ctx = application_context(tenant_id, app_id)
        plan = _use_cases().get_active(ctx, GetActiveMarketingPlanQuery())
        return success(plan_to_response(plan) if plan else None)

    @app.get(f"{base}/marketing-plans/<plan_id>")
    @auth_decorator
    @_handle_application_errors
    def api_get_marketing_plan(tenant_id: str, app_id: str, plan_id: str):
        ctx = application_context(tenant_id, app_id)
        plan = _use_cases().get(ctx, GetMarketingPlanQuery(plan_id=plan_id))
        return success(plan_to_response(plan))

    @app.post(f"{base}/marketing-plans/<plan_id>/activate")
    @auth_decorator
    @_handle_application_errors
    def api_activate_marketing_plan(tenant_id: str, app_id: str, plan_id: str):
        body = request.get_json(silent=True) or {}
        ctx = application_context(tenant_id, app_id)
        result = _use_cases().activate(ctx, activate_input_from_json(plan_id, body))
        return success(plan_to_response(result.plan))

    @app.get(f"{base}/marketing-context")
    @auth_decorator
    def api_marketing_context(tenant_id: str, app_id: str):
        ctx = application_context(tenant_id, app_id)
        data = build_marketing_context(
            tenant_id,
            app_id,
            actor_id=ctx.actor_id,
            actor_role=ctx.actor_role,
        )
        return success(data)

    @app.post(f"{base}/planner/proposals")
    @auth_decorator
    def api_planner_proposals(tenant_id: str, app_id: str):
        ctx = application_context(tenant_id, app_id)
        data = generate_proposals(
            tenant_id,
            app_id,
            actor_id=ctx.actor_id,
            actor_role=ctx.actor_role,
        )
        return success(data)
