from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Union

from .enums import PlanPriority, PlanStatus, StrategyType

SuccessCriteria = Union[str, list[str]]
TargetAudience = Union[str, list[str]]


@dataclass
class DateRange:
    inicio: date
    fin: date


@dataclass
class Budget:
    amount: Decimal
    currency: str


@dataclass
class MarketingPlan:
    id: str
    tenant_id: str
    app_id: str
    nombre: str
    objetivo_general: str
    strategy_type: StrategyType
    north_star_metric: str
    success_criteria: SuccessCriteria
    publico_objetivo: TargetAudience
    marketing_brief: str
    periodo: DateRange
    budget: Budget
    estado: PlanStatus
    prioridad: PlanPriority
    created_at: datetime
    updated_at: datetime
    created_by: str
    observaciones: str = ""
    activated_at: datetime | None = None

    def copy(self) -> MarketingPlan:
        return MarketingPlan(
            id=self.id,
            tenant_id=self.tenant_id,
            app_id=self.app_id,
            nombre=self.nombre,
            objetivo_general=self.objetivo_general,
            strategy_type=self.strategy_type,
            north_star_metric=self.north_star_metric,
            success_criteria=self.success_criteria,
            publico_objetivo=self.publico_objetivo,
            marketing_brief=self.marketing_brief,
            periodo=DateRange(self.periodo.inicio, self.periodo.fin),
            budget=Budget(self.budget.amount, self.budget.currency),
            estado=self.estado,
            prioridad=self.prioridad,
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            observaciones=self.observaciones,
            activated_at=self.activated_at,
        )


FORBIDDEN_PLAN_FIELDS = frozenset(
    {
        "provider",
        "model",
        "prompt",
        "consumer",
        "publicaciones",
        "posts",
        "calendario",
        "campanas",
        "campaigns",
        "assets",
        "leads",
        "metricas",
        "metrics",
        "ai_provider",
        "ai_model",
        "ai_prompt",
        "dashboard_config",
    }
)
