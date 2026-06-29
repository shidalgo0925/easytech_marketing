from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.campaign_application.context import TenantAppContext


class AuthorizationPort(Protocol):
    def require_permission(self, ctx: TenantAppContext, action: str) -> None:
        ...
