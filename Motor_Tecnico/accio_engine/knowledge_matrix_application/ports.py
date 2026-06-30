from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.knowledge_matrix_application.context import TenantContext


class AuthorizationPort(Protocol):
    def require_permission(self, ctx: TenantContext, action: str) -> None: ...
