from __future__ import annotations

from Motor_Tecnico.accio_engine.opportunity_application.context import TenantContext
from Motor_Tecnico.accio_engine.opportunity_application.ports import AuthorizationPort


class OpportunityRbacAdapter:
    def require_permission(self, ctx: TenantContext, action: str) -> None:
        from Motor_Tecnico.accio_engine.app import _check_request_permission, _user_can_access_tenant

        if not _user_can_access_tenant(ctx.tenant_id):
            raise PermissionError(f"Sin acceso al tenant {ctx.tenant_id}")
        ok, _ = _check_request_permission(action)
        if not ok:
            raise PermissionError(f"Permiso denegado: {action}")
