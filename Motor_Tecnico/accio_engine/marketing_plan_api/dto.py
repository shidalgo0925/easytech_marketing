"""DTOs API ↔ Application (Vertical Slice 1)."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.marketing_plan_application.command_inputs import (
    ActivateMarketingPlanInput,
    CreateMarketingPlanInput,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import ConflictResolution
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan


def plan_to_response(plan: MarketingPlan) -> dict[str, Any]:
    return {
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
        "created_at": _dt(plan.created_at),
        "updated_at": _dt(plan.updated_at),
        "created_by": plan.created_by,
        "activated_at": _dt(plan.activated_at) if plan.activated_at else None,
    }


def _dt(value) -> str:
    if value.tzinfo is None:
        return value.isoformat() + "Z"
    return value.astimezone().isoformat().replace("+00:00", "Z")


def create_input_from_json(body: dict[str, Any]) -> CreateMarketingPlanInput:
    periodo = body.get("periodo") or {}
    budget = body.get("budget") or {}
    return CreateMarketingPlanInput(
        nombre=str(body.get("nombre") or ""),
        objetivo_general=str(body.get("objetivo_general") or ""),
        strategy_type=str(body.get("strategy_type") or ""),
        north_star_metric=str(body.get("north_star_metric") or ""),
        success_criteria=body.get("success_criteria") or [],
        publico_objetivo=body.get("publico_objetivo") or [],
        marketing_brief=str(body.get("marketing_brief") or ""),
        periodo_inicio=periodo.get("inicio") or body.get("periodo_inicio") or "",
        periodo_fin=periodo.get("fin") or body.get("periodo_fin") or "",
        budget_amount=(budget.get("amount") if budget else body.get("budget_amount")) or "0",
        budget_currency=str((budget.get("currency") if budget else body.get("budget_currency")) or "USD"),
        prioridad=str(body.get("prioridad") or "media"),
        observaciones=str(body.get("observaciones") or ""),
        extra_fields={
            k: v
            for k, v in body.items()
            if k
            not in {
                "nombre",
                "objetivo_general",
                "strategy_type",
                "north_star_metric",
                "success_criteria",
                "publico_objetivo",
                "marketing_brief",
                "periodo",
                "budget",
                "prioridad",
                "observaciones",
            }
        },
    )


def activate_input_from_json(plan_id: str, body: dict[str, Any] | None) -> ActivateMarketingPlanInput:
    body = body or {}
    resolution = body.get("resolution")
    parsed = ConflictResolution(str(resolution)) if resolution else None
    return ActivateMarketingPlanInput(plan_id=plan_id, resolution=parsed)
