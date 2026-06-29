from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import AuthorizationPort


def require_read(ctx: ApplicationContext, authorization: AuthorizationPort) -> None:
    authorization.require_permission(ctx, "read")


def require_config_or_admin(ctx: ApplicationContext, authorization: AuthorizationPort) -> None:
    if authorization.has_permission(ctx, "config") or authorization.has_permission(ctx, "admin"):
        return
    raise ApplicationError.forbidden("Se requiere permiso config o admin")


def require_admin(ctx: ApplicationContext, authorization: AuthorizationPort) -> None:
    authorization.require_permission(ctx, "admin")
