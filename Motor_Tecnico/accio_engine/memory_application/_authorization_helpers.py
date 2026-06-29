from __future__ import annotations

from Motor_Tecnico.accio_engine.memory_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.memory_application.ports import AuthorizationPort


def require_read(ctx: TenantContext, authorization: AuthorizationPort) -> None:
    authorization.require_permission(ctx, "read")
