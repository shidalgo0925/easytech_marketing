from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.campaign_application.context import TenantAppContext


class TenantAccessContext(Protocol):
    tenant_id: str


class AuthorizationPort(Protocol):
    def require_permission(self, ctx: TenantAccessContext, action: str) -> None:
        ...
