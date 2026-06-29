"""RBAC adapter for Corporate Memory API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine import rbac
from Motor_Tecnico.accio_engine.memory_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.memory_application.ports import AuthorizationPort


class MemoryRbacAuthorizationAdapter:
    def has_permission(self, ctx: TenantContext, permission: str) -> bool:
        return rbac.has_permission(ctx.actor_role, permission, ctx.tenant_id)

    def require_permission(self, ctx: TenantContext, permission: str) -> None:
        if not self.has_permission(ctx, permission):
            raise ApplicationError.forbidden(f"Permiso requerido: {permission}")
