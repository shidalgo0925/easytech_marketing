"""Mapeo MarketingPlan ↔ registro persistible (dict). Sin reglas de negocio."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import PlanPriority, PlanStatus, StrategyType
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import (
    Budget,
    DateRange,
    MarketingPlan,
    SuccessCriteria,
    TargetAudience,
)

PERSISTENCE_SCHEMA_VERSION = 1


def plan_to_record(plan: MarketingPlan) -> dict[str, Any]:
    return {
        "persistence_schema_version": PERSISTENCE_SCHEMA_VERSION,
        "id": plan.id,
        "tenant_id": plan.tenant_id,
        "app_id": plan.app_id,
        "nombre": plan.nombre,
        "objetivo_general": plan.objetivo_general,
        "strategy_type": plan.strategy_type.value,
        "north_star_metric": plan.north_star_metric,
        "success_criteria": plan.success_criteria,
        "publico_objetivo": plan.publico_objetivo,
        "marketing_brief": plan.marketing_brief,
        "periodo": {
            "inicio": plan.periodo.inicio.isoformat(),
            "fin": plan.periodo.fin.isoformat(),
        },
        "budget": {
            "amount": str(plan.budget.amount),
            "currency": plan.budget.currency,
        },
        "estado": plan.estado.value,
        "prioridad": plan.prioridad.value,
        "observaciones": plan.observaciones,
        "created_at": _dt_to_str(plan.created_at),
        "updated_at": _dt_to_str(plan.updated_at),
        "created_by": plan.created_by,
        "activated_at": _dt_to_str(plan.activated_at) if plan.activated_at else None,
    }


def record_to_plan(record: dict[str, Any]) -> MarketingPlan:
    return MarketingPlan(
        id=str(record["id"]),
        tenant_id=str(record["tenant_id"]),
        app_id=str(record["app_id"]),
        nombre=str(record["nombre"]),
        objetivo_general=str(record["objetivo_general"]),
        strategy_type=StrategyType(str(record["strategy_type"])),
        north_star_metric=str(record["north_star_metric"]),
        success_criteria=_parse_union_text_list(record["success_criteria"]),
        publico_objetivo=_parse_union_text_list(record["publico_objetivo"]),
        marketing_brief=str(record["marketing_brief"]),
        periodo=DateRange(
            inicio=date.fromisoformat(str(record["periodo"]["inicio"])),
            fin=date.fromisoformat(str(record["periodo"]["fin"])),
        ),
        budget=Budget(
            amount=Decimal(str(record["budget"]["amount"])),
            currency=str(record["budget"]["currency"]),
        ),
        estado=PlanStatus(str(record["estado"])),
        prioridad=PlanPriority(str(record["prioridad"])),
        observaciones=str(record.get("observaciones") or ""),
        created_at=_parse_datetime(record["created_at"]),
        updated_at=_parse_datetime(record["updated_at"]),
        created_by=str(record["created_by"]),
        activated_at=_parse_datetime(record["activated_at"]) if record.get("activated_at") else None,
    )


def _parse_union_text_list(value: SuccessCriteria | TargetAudience) -> SuccessCriteria | TargetAudience:
    if isinstance(value, list):
        return [str(item) for item in value]
    return str(value)


def _dt_to_str(value: datetime) -> str:
    if value.tzinfo is None:
        return value.isoformat()
    return value.astimezone().isoformat()


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(str(value))
