from __future__ import annotations

from Motor_Tecnico.accio_engine import rbac
from Motor_Tecnico.accio_engine.brand_application.context import TenantContext
from Motor_Tecnico.accio_engine.brand_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.brand_application.ports import AuthorizationPort


class BrandRbacAdapter:
    def require_permission(self, ctx: TenantContext, permission: str) -> None:
        if not rbac.has_permission(ctx.actor_role, permission, ctx.tenant_id):
            raise ApplicationError.forbidden(f"Permiso requerido: {permission}")
