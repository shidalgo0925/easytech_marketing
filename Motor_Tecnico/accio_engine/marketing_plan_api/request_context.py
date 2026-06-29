"""ApplicationContext desde request Flask (Vertical Slice 1)."""

from __future__ import annotations

from flask import session

from Motor_Tecnico.accio_engine import auth_service
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext


def session_role(tenant_id: str) -> str:
    if session.get("auth_method") == "api_key":
        return "admin"
    if session.get("global_role") == "super_admin":
        return "super_admin"
    user_id = session.get("user_id")
    if user_id:
        role = auth_service.get_tenant_role(user_id, tenant_id, session.get("global_role"))
        if role:
            return role
    role = session.get("role")
    if role and session.get("tenant_id") == tenant_id:
        return role
    return "viewer"


def application_context(tenant_id: str, app_id: str) -> ApplicationContext:
    actor_id = str(session.get("user_id") or session.get("email") or "api")
    return ApplicationContext(
        tenant_id=tenant_id,
        app_id=app_id,
        actor_id=actor_id,
        actor_role=session_role(tenant_id),
    )
