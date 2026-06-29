from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .enums import PlanStatus
from .model import MarketingPlan


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_plan_id(self) -> str: ...

    def new_event_id(self) -> str: ...


class TenantAppValidator(Protocol):
    def tenant_exists(self, tenant_id: str) -> bool: ...

    def app_exists(self, tenant_id: str, app_id: str) -> bool: ...


class MarketingPlanRepository(Protocol):
    def get_by_id(self, plan_id: str) -> MarketingPlan | None: ...

    def save(self, plan: MarketingPlan) -> None: ...

    def find_active(self, tenant_id: str, app_id: str) -> MarketingPlan | None: ...

    def list_plans(
        self,
        tenant_id: str,
        *,
        app_id: str | None = None,
        estado: PlanStatus | None = None,
    ) -> list[MarketingPlan]: ...
