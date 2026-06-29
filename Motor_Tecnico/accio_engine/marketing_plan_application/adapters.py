"""Adaptadores de infraestructura para la Application Layer."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import (
    AuthorizationPort,
    DomainEventPublisher,
    TenantAppContextPort,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.events import DomainEvent


class AllowAllAuthorization:
    def has_permission(self, ctx: ApplicationContext, permission: str) -> bool:
        return True

    def require_permission(self, ctx: ApplicationContext, permission: str) -> None:
        return None


class RoleBasedAuthorization:
    def __init__(self, permissions_by_role: dict[str, set[str]]) -> None:
        self._permissions_by_role = permissions_by_role

    def has_permission(self, ctx: ApplicationContext, permission: str) -> bool:
        perms = self._permissions_by_role.get(ctx.actor_role, set())
        return permission in perms or "admin" in perms

    def require_permission(self, ctx: ApplicationContext, permission: str) -> None:
        if not self.has_permission(ctx, permission):
            raise ApplicationError.forbidden(f"Permiso requerido: {permission}")


class NoOpWorkspace:
    def ensure_workspace(self, ctx: ApplicationContext) -> None:
        return None


class NoOpDomainEventPublisher:
    def publish(self, events: list[DomainEvent]) -> None:
        return None


class CollectingDomainEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)
