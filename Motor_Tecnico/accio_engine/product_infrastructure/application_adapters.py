from __future__ import annotations

from Motor_Tecnico.accio_engine.product_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.product_application.ports import AuthorizationPort


class ProductRbacAdapter:
    def require_permission(self, ctx: TenantAppContext, action: str) -> None:
        from Motor_Tecnico.accio_engine.app import _check_request_permission, _user_can_access_tenant

        if not _user_can_access_tenant(ctx.tenant_id):
            raise PermissionError(f"Sin acceso al tenant {ctx.tenant_id}")
        ok, _ = _check_request_permission(action)
        if not ok:
            raise PermissionError(f"Permiso denegado: {action}")
