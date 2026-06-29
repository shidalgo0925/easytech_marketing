from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any

from .enums import PlanPriority, PlanStatus, StrategyType
from .errors import DomainError, DomainErrorCode
from .model import Budget, DateRange, FORBIDDEN_PLAN_FIELDS, MarketingPlan, SuccessCriteria, TargetAudience

_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
_OPERATIONAL_KEYWORDS = (
    "publicar",
    "programar",
    "encolar",
    "ejecutar",
    "cron",
    "schedule post",
)


def reject_forbidden_fields(payload: dict[str, Any]) -> None:
    forbidden = FORBIDDEN_PLAN_FIELDS.intersection(payload.keys())
    if forbidden:
        raise DomainError(
            DomainErrorCode.FORBIDDEN_FIELD,
            f"Campos prohibidos en el agregado: {', '.join(sorted(forbidden))}",
            {"fields": sorted(forbidden)},
        )


def parse_strategy_type(value: StrategyType | str) -> StrategyType:
    if isinstance(value, StrategyType):
        return value
    try:
        return StrategyType(str(value))
    except ValueError as exc:
        raise DomainError(
            DomainErrorCode.STRATEGY_TYPE_INVALID,
            f"strategy_type inválido: {value!r}",
        ) from exc


def parse_plan_priority(value: PlanPriority | str) -> PlanPriority:
    if isinstance(value, PlanPriority):
        return value
    try:
        return PlanPriority(str(value))
    except ValueError as exc:
        raise DomainError(
            DomainErrorCode.PRIORITY_INVALID,
            f"prioridad inválida: {value!r}",
        ) from exc


def validate_date_range(periodo: DateRange) -> None:
    if periodo.fin < periodo.inicio:
        raise DomainError(
            DomainErrorCode.INVALID_DATE_RANGE,
            "periodo.fin debe ser mayor o igual que periodo.inicio",
            {"inicio": periodo.inicio.isoformat(), "fin": periodo.fin.isoformat()},
        )


def validate_budget(budget: Budget) -> None:
    if budget.amount < 0:
        raise DomainError(
            DomainErrorCode.BUDGET_INVALID,
            "budget.amount no puede ser negativo",
            {"amount": str(budget.amount)},
        )
    if not _CURRENCY_RE.match(budget.currency):
        raise DomainError(
            DomainErrorCode.CURRENCY_INVALID,
            "budget.currency debe ser ISO 4217 (3 letras mayúsculas)",
            {"currency": budget.currency},
        )


def _validate_text_length(
    value: str,
    *,
    field_name: str,
    min_len: int,
    max_len: int,
    code: DomainErrorCode,
) -> str:
    text = value.strip()
    if len(text) < min_len or len(text) > max_len:
        raise DomainError(
            code,
            f"{field_name} debe tener entre {min_len} y {max_len} caracteres",
            {"length": len(text)},
        )
    return text


def validate_success_criteria(value: SuccessCriteria) -> SuccessCriteria:
    if isinstance(value, str):
        text = value.strip()
        if len(text) < 10 or len(text) > 3000:
            raise DomainError(
                DomainErrorCode.SUCCESS_CRITERIA_INVALID,
                "success_criteria (string) debe tener entre 10 y 3000 caracteres",
            )
        return text
    if not isinstance(value, list) or not (1 <= len(value) <= 20):
        raise DomainError(
            DomainErrorCode.SUCCESS_CRITERIA_INVALID,
            "success_criteria (lista) debe tener entre 1 y 20 items",
        )
    cleaned = [item.strip() for item in value]
    if any(not item for item in cleaned):
        raise DomainError(
            DomainErrorCode.SUCCESS_CRITERIA_INVALID,
            "success_criteria no puede contener items vacíos",
        )
    return cleaned


def validate_target_audience(value: TargetAudience) -> TargetAudience:
    if isinstance(value, str):
        text = value.strip()
        if len(text) < 3 or len(text) > 2000:
            raise DomainError(
                DomainErrorCode.TARGET_AUDIENCE_INVALID,
                "publico_objetivo (string) debe tener entre 3 y 2000 caracteres",
            )
        return text
    if not isinstance(value, list) or not (1 <= len(value) <= 15):
        raise DomainError(
            DomainErrorCode.TARGET_AUDIENCE_INVALID,
            "publico_objetivo (lista) debe tener entre 1 y 15 items",
        )
    cleaned = [item.strip() for item in value]
    if any(not item for item in cleaned):
        raise DomainError(
            DomainErrorCode.TARGET_AUDIENCE_INVALID,
            "publico_objetivo no puede contener items vacíos",
        )
    return cleaned


def validate_declarative_content(objetivo_general: str, marketing_brief: str) -> None:
    combined = f"{objetivo_general} {marketing_brief}".lower()
    hits = sum(1 for keyword in _OPERATIONAL_KEYWORDS if keyword in combined)
    if hits >= 2:
        raise DomainError(
            DomainErrorCode.PLAN_NOT_DECLARATIVE,
            "El plan contiene demasiadas instrucciones operativas (R3)",
            {"operational_signals": hits},
        )


def validate_plan_fields(plan: MarketingPlan) -> None:
    if not plan.tenant_id.strip():
        raise DomainError(DomainErrorCode.TENANT_REQUIRED, "tenant_id es obligatorio")
    if not plan.app_id.strip():
        raise DomainError(DomainErrorCode.APP_REQUIRED, "app_id es obligatorio")
    if not plan.created_by.strip():
        raise DomainError(DomainErrorCode.CREATOR_REQUIRED, "created_by es obligatorio")

    plan.nombre = _validate_text_length(
        plan.nombre,
        field_name="nombre",
        min_len=3,
        max_len=120,
        code=DomainErrorCode.NAME_INVALID,
    )
    plan.objetivo_general = _validate_text_length(
        plan.objetivo_general,
        field_name="objetivo_general",
        min_len=10,
        max_len=2000,
        code=DomainErrorCode.OBJECTIVE_INVALID,
    )
    plan.north_star_metric = _validate_text_length(
        plan.north_star_metric,
        field_name="north_star_metric",
        min_len=3,
        max_len=500,
        code=DomainErrorCode.NORTH_STAR_REQUIRED,
    )
    plan.marketing_brief = _validate_text_length(
        plan.marketing_brief,
        field_name="marketing_brief",
        min_len=10,
        max_len=50000,
        code=DomainErrorCode.BRIEF_REQUIRED,
    )
    if plan.observaciones and len(plan.observaciones) > 2000:
        raise DomainError(
            DomainErrorCode.NOTES_TOO_LONG,
            "observaciones no puede superar 2000 caracteres",
        )

    plan.success_criteria = validate_success_criteria(plan.success_criteria)
    plan.publico_objetivo = validate_target_audience(plan.publico_objetivo)
    validate_date_range(plan.periodo)
    validate_budget(plan.budget)
    validate_declarative_content(plan.objetivo_general, plan.marketing_brief)

    if plan.estado == PlanStatus.ACTIVO and plan.activated_at is None:
        raise DomainError(
            DomainErrorCode.ACTIVATED_AT_REQUIRED,
            "activated_at es obligatorio cuando estado=activo",
        )


def ensure_editable(plan: MarketingPlan) -> None:
    if plan.estado == PlanStatus.FINALIZADO:
        raise DomainError(
            DomainErrorCode.PLAN_COMPLETED,
            "Un plan finalizado no puede modificarse",
            {"plan_id": plan.id},
        )
    if plan.estado not in (PlanStatus.BORRADOR, PlanStatus.PAUSADO):
        raise DomainError(
            DomainErrorCode.PLAN_NOT_EDITABLE,
            "Solo se puede editar un plan en borrador o pausado",
            {"plan_id": plan.id, "estado": plan.estado.value},
        )


def coerce_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def coerce_decimal(value: Decimal | int | float | str) -> Decimal:
    return Decimal(str(value))
