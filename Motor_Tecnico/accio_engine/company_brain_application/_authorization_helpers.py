from __future__ import annotations

from Motor_Tecnico.accio_engine.company_brain_application.context import TenantContext
from Motor_Tecnico.accio_engine.company_brain_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.company_brain_application.ports import AuthorizationPort


def require_read(ctx: TenantContext, authorization: AuthorizationPort) -> None:
    authorization.require_permission(ctx, "read")


def require_config_or_admin(ctx: TenantContext, authorization: AuthorizationPort) -> None:
    if authorization.has_permission(ctx, "config") or authorization.has_permission(ctx, "admin"):
        return
    raise ApplicationError.forbidden("Se requiere permiso config o admin")
