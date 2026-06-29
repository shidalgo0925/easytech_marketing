from __future__ import annotations

from dataclasses import dataclass

from Motor_Tecnico.accio_engine.marketing_plan_domain.events import DomainEvent
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan


@dataclass(frozen=True)
class CommandResult:
    plan: MarketingPlan
    events: list[DomainEvent]
