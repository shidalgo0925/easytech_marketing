from __future__ import annotations

from typing import Protocol

from .context import TenantContext


class AuthorizationPort(Protocol):
    def require_permission(self, ctx: TenantContext, permission: str) -> None: ...
