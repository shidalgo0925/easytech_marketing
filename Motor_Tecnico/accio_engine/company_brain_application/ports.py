from __future__ import annotations

from typing import Protocol

from .context import TenantContext


class AuthorizationPort(Protocol):
    def has_permission(self, ctx: TenantContext, permission: str) -> bool: ...

    def require_permission(self, ctx: TenantContext, permission: str) -> None: ...
