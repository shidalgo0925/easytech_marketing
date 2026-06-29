"""Stubs en memoria — implementan puertos del dominio MarketingPlan."""

from __future__ import annotations

from datetime import datetime

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import PlanStatus
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan


class InMemoryMarketingPlanRepository:
    def __init__(self) -> None:
        self._plans: dict[str, MarketingPlan] = {}

    def get_by_id(self, plan_id: str) -> MarketingPlan | None:
        plan = self._plans.get(plan_id)
        return plan.copy() if plan else None

    def save(self, plan: MarketingPlan) -> None:
        self._plans[plan.id] = plan.copy()

    def find_active(self, tenant_id: str, app_id: str) -> MarketingPlan | None:
        for plan in self._plans.values():
            if (
                plan.tenant_id == tenant_id
                and plan.app_id == app_id
                and plan.estado == PlanStatus.ACTIVO
            ):
                return plan.copy()
        return None

    def list_plans(
        self,
        tenant_id: str,
        *,
        app_id: str | None = None,
        estado: PlanStatus | None = None,
    ) -> list[MarketingPlan]:
        rows: list[MarketingPlan] = []
        for plan in self._plans.values():
            if plan.tenant_id != tenant_id:
                continue
            if app_id is not None and plan.app_id != app_id:
                continue
            if estado is not None and plan.estado != estado:
                continue
            rows.append(plan.copy())
        rows.sort(key=lambda p: p.created_at)
        return rows


class FixedClock:
    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


class FixedIdGenerator:
    def __init__(self, plan_ids: list[str] | None = None, event_ids: list[str] | None = None) -> None:
        self._plan_ids = list(plan_ids or [])
        self._event_ids = list(event_ids or [])
        self._plan_idx = 0
        self._event_idx = 0

    def new_plan_id(self) -> str:
        if self._plan_idx < len(self._plan_ids):
            value = self._plan_ids[self._plan_idx]
            self._plan_idx += 1
            return value
        value = f"mpl_{self._plan_idx:04d}"
        self._plan_idx += 1
        return value

    def new_event_id(self) -> str:
        if self._event_idx < len(self._event_ids):
            value = self._event_ids[self._event_idx]
            self._event_idx += 1
            return value
        value = f"evt_{self._event_idx:04d}"
        self._event_idx += 1
        return value
