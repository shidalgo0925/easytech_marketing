from __future__ import annotations

from dataclasses import dataclass

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import PlanStatus


@dataclass(frozen=True)
class GetMarketingPlanQuery:
    plan_id: str


@dataclass(frozen=True)
class GetActiveMarketingPlanQuery:
    pass


@dataclass(frozen=True)
class ListMarketingPlansQuery:
    app_id: str | None = None
    estado: PlanStatus | None = None
