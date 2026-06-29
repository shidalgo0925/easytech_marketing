from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.marketing_plan_domain.events import DomainEvent

from .context import ApplicationContext


class AuthorizationPort(Protocol):
    def has_permission(self, ctx: ApplicationContext, permission: str) -> bool: ...

    def require_permission(self, ctx: ApplicationContext, permission: str) -> None: ...


class TenantAppContextPort(Protocol):
    def ensure_workspace(self, ctx: ApplicationContext) -> None: ...


class DomainEventPublisher(Protocol):
    def publish(self, events: list[DomainEvent]) -> None: ...
