from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import ConflictResolution, PlanPriority, StrategyType
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import SuccessCriteria, TargetAudience


@dataclass(frozen=True)
class CreateMarketingPlanInput:
    nombre: str
    objetivo_general: str
    strategy_type: StrategyType | str
    north_star_metric: str
    success_criteria: SuccessCriteria
    publico_objetivo: TargetAudience
    marketing_brief: str
    periodo_inicio: date | str
    periodo_fin: date | str
    budget_amount: Decimal | int | float | str
    budget_currency: str
    prioridad: PlanPriority | str
    observaciones: str = ""
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateMarketingPlanInput:
    plan_id: str
    nombre: str | None = None
    objetivo_general: str | None = None
    strategy_type: StrategyType | str | None = None
    north_star_metric: str | None = None
    success_criteria: SuccessCriteria | None = None
    publico_objetivo: TargetAudience | None = None
    marketing_brief: str | None = None
    periodo_inicio: date | str | None = None
    periodo_fin: date | str | None = None
    budget_amount: Decimal | int | float | str | None = None
    budget_currency: str | None = None
    prioridad: PlanPriority | str | None = None
    observaciones: str | None = None
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivateMarketingPlanInput:
    plan_id: str
    resolution: ConflictResolution | None = None


@dataclass(frozen=True)
class PauseMarketingPlanInput:
    plan_id: str


@dataclass(frozen=True)
class CompleteMarketingPlanInput:
    plan_id: str
