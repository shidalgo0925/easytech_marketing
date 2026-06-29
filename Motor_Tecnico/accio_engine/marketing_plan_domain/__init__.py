"""Dominio MarketingPlan — Pieza 3 (servicio + puertos; sin API/UI/persistencia)."""

from .errors import DomainError, DomainErrorCode
from .events import (
    DomainEvent,
    PlanActivated,
    PlanCompleted,
    PlanCreated,
    PlanPaused,
)
from .model import Budget, DateRange, MarketingPlan
from .service import MarketingPlanDomainService, MutationResult

__all__ = [
    "Budget",
    "DateRange",
    "DomainError",
    "DomainErrorCode",
    "DomainEvent",
    "MarketingPlan",
    "MarketingPlanDomainService",
    "MutationResult",
    "PlanActivated",
    "PlanCompleted",
    "PlanCreated",
    "PlanPaused",
]
