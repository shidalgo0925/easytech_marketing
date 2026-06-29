"""Adaptadores para puertos de la Application Layer."""

from __future__ import annotations

from Motor_Tecnico.accio_engine import rbac
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError


class RbacAuthorizationAdapter:
    def has_permission(self, ctx: ApplicationContext, permission: str) -> bool:
        return rbac.has_permission(ctx.actor_role, permission, ctx.tenant_id)

    def require_permission(self, ctx: ApplicationContext, permission: str) -> None:
        if not self.has_permission(ctx, permission):
            raise ApplicationError.forbidden(f"Permiso requerido: {permission}")
