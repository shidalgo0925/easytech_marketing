"""Composition root — Vertical Slice 1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.marketing_plan_application.adapters import (
    CollectingDomainEventPublisher,
    NoOpDomainEventPublisher,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.commands.activate_marketing_plan import (
    ActivateMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.commands.create_marketing_plan import (
    CreateMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.queries.get_active_marketing_plan import (
    GetActiveMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.queries.get_marketing_plan import (
    GetMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.application_adapters import (
    RbacAuthorizationAdapter,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.json_repository import (
    JsonMarketingPlanRepository,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled
from Motor_Tecnico.accio_engine.tenant import TENANTS_ROOT, resolve_tenant


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UuidIdGenerator:
    def new_plan_id(self) -> str:
        return f"mpl_{uuid.uuid4().hex[:12]}"

    def new_event_id(self) -> str:
        return f"evt_{uuid.uuid4().hex[:12]}"


class MarketingAppWorkspaceAdapter:
    def ensure_workspace(self, ctx: ApplicationContext) -> None:
        resolve_tenant(ctx.tenant_id)
        marketing_app.get_app(ctx.tenant_id, ctx.app_id)


class MarketingTenantAppValidator:
    def tenant_exists(self, tenant_id: str) -> bool:
        try:
            resolve_tenant(tenant_id)
            return True
        except Exception:
            return False

    def app_exists(self, tenant_id: str, app_id: str) -> bool:
        try:
            marketing_app.get_app(tenant_id, app_id)
            return True
        except Exception:
            return False


def build_domain_service() -> MarketingPlanDomainService:
    return MarketingPlanDomainService(
        repository=JsonMarketingPlanRepository(TENANTS_ROOT),
        clock=SystemClock(),
        id_generator=UuidIdGenerator(),
        tenant_app_validator=MarketingTenantAppValidator(),
    )


def build_event_publisher():
    if memory_sql_enabled():
        from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
        from Motor_Tecnico.accio_engine.memory_infrastructure.marketing_plan_bridge import (
            MarketingPlanMemoryEventPublisher,
        )

        return MarketingPlanMemoryEventPublisher(get_memory_domain_service())
    return NoOpDomainEventPublisher()


class MarketingPlanUseCases:
    def __init__(self, *, events: CollectingDomainEventPublisher | None = None) -> None:
        domain = build_domain_service()
        auth = RbacAuthorizationAdapter()
        workspace = MarketingAppWorkspaceAdapter()
        publisher = events if events is not None else build_event_publisher()
        self.create = CreateMarketingPlan(domain, auth, workspace, publisher)
        self.activate = ActivateMarketingPlan(domain, auth, workspace, publisher)
        self.get = GetMarketingPlan(domain, auth, workspace)
        self.get_active = GetActiveMarketingPlan(domain, auth, workspace)


_USE_CASES: MarketingPlanUseCases | None = None


def marketing_plan_use_cases() -> MarketingPlanUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = MarketingPlanUseCases()
    return _USE_CASES


def reset_marketing_plan_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None
