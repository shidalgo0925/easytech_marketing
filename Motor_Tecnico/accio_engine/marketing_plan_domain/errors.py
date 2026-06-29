from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DomainErrorCode(str, Enum):
    PLAN_NOT_FOUND = "PlanNotFound"
    PLAN_COMPLETED = "PlanCompleted"
    STRATEGY_TYPE_INVALID = "StrategyTypeInvalid"
    INVALID_DATE_RANGE = "InvalidDateRange"
    ACTIVE_PLAN_RESOLUTION_REQUIRED = "ActivePlanResolutionRequired"
    BUDGET_INVALID = "BudgetInvalid"
    INVALID_STATUS_TRANSITION = "InvalidStatusTransition"
    PLAN_NOT_DECLARATIVE = "PlanNotDeclarative"
    FORBIDDEN_FIELD = "ForbiddenField"
    TENANT_REQUIRED = "TenantRequired"
    APP_REQUIRED = "AppRequired"
    TENANT_NOT_FOUND = "TenantNotFound"
    APP_NOT_FOUND = "AppNotFound"
    NAME_INVALID = "NameInvalid"
    OBJECTIVE_INVALID = "ObjectiveInvalid"
    NORTH_STAR_REQUIRED = "NorthStarRequired"
    SUCCESS_CRITERIA_INVALID = "SuccessCriteriaInvalid"
    TARGET_AUDIENCE_INVALID = "TargetAudienceInvalid"
    BRIEF_REQUIRED = "BriefRequired"
    CURRENCY_INVALID = "CurrencyInvalid"
    STATUS_INVALID = "StatusInvalid"
    PRIORITY_INVALID = "PriorityInvalid"
    NOTES_TOO_LONG = "NotesTooLong"
    CREATOR_REQUIRED = "CreatorRequired"
    ACTIVATED_AT_REQUIRED = "ActivatedAtRequired"
    PLAN_NOT_EDITABLE = "PlanNotEditable"


@dataclass(frozen=True)
class DomainError(Exception):
    code: DomainErrorCode
    message: str
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
