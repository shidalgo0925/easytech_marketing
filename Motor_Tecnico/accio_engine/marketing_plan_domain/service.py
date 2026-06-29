from __future__ import annotations

from dataclasses import dataclass

from .commands import (
    ActivatePlanCommand,
    CompletePlanCommand,
    CreatePlanCommand,
    PausePlanCommand,
    UpdatePlanCommand,
)
from .enums import ALLOWED_TRANSITIONS, ConflictResolution, PlanStatus
from .errors import DomainError, DomainErrorCode
from .events import (
    DomainEvent,
    PlanActivated,
    PlanCompleted,
    PlanCreated,
    PlanPaused,
    RESOLUTION_TO_EVENT,
)
from .defaults import AcceptAllTenantAppValidator
from .model import Budget, DateRange, MarketingPlan
from .ports import Clock, IdGenerator, MarketingPlanRepository, TenantAppValidator
from .validators import (
    coerce_date,
    coerce_decimal,
    ensure_editable,
    parse_plan_priority,
    parse_strategy_type,
    reject_forbidden_fields,
    validate_plan_fields,
)


@dataclass
class MutationResult:
    plan: MarketingPlan
    events: list[DomainEvent]


class MarketingPlanDomainService:
    def __init__(
        self,
        repository: MarketingPlanRepository,
        clock: Clock,
        id_generator: IdGenerator,
        tenant_app_validator: TenantAppValidator | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._ids = id_generator
        self._tenant_apps = tenant_app_validator or AcceptAllTenantAppValidator()

    def create_plan(self, command: CreatePlanCommand) -> MutationResult:
        reject_forbidden_fields(command.extra_fields)
        self._ensure_tenant_app(command.tenant_id, command.app_id)

        now = self._clock.now()
        plan = MarketingPlan(
            id=self._ids.new_plan_id(),
            tenant_id=command.tenant_id.strip(),
            app_id=command.app_id.strip(),
            nombre=command.nombre,
            objetivo_general=command.objetivo_general,
            strategy_type=parse_strategy_type(command.strategy_type),
            north_star_metric=command.north_star_metric,
            success_criteria=command.success_criteria,
            publico_objetivo=command.publico_objetivo,
            marketing_brief=command.marketing_brief,
            periodo=DateRange(
                coerce_date(command.periodo_inicio),
                coerce_date(command.periodo_fin),
            ),
            budget=Budget(
                coerce_decimal(command.budget_amount),
                command.budget_currency.strip().upper(),
            ),
            estado=PlanStatus.BORRADOR,
            prioridad=parse_plan_priority(command.prioridad),
            created_at=now,
            updated_at=now,
            created_by=command.created_by.strip(),
            observaciones=command.observaciones or "",
            activated_at=None,
        )
        validate_plan_fields(plan)
        self._repository.save(plan)

        event = PlanCreated(
            event_id=self._ids.new_event_id(),
            occurred_at=now,
            plan_id=plan.id,
            tenant_id=plan.tenant_id,
            app_id=plan.app_id,
            estado=plan.estado,
            created_by=plan.created_by,
        )
        return MutationResult(plan=plan.copy(), events=[event])

    def update_plan(self, command: UpdatePlanCommand) -> MutationResult:
        reject_forbidden_fields(command.extra_fields)
        plan = self._require_plan(command.plan_id, command.tenant_id)
        ensure_editable(plan)

        if command.nombre is not None:
            plan.nombre = command.nombre
        if command.objetivo_general is not None:
            plan.objetivo_general = command.objetivo_general
        if command.strategy_type is not None:
            plan.strategy_type = parse_strategy_type(command.strategy_type)
        if command.north_star_metric is not None:
            plan.north_star_metric = command.north_star_metric
        if command.success_criteria is not None:
            plan.success_criteria = command.success_criteria
        if command.publico_objetivo is not None:
            plan.publico_objetivo = command.publico_objetivo
        if command.marketing_brief is not None:
            plan.marketing_brief = command.marketing_brief
        if command.periodo_inicio is not None or command.periodo_fin is not None:
            inicio = coerce_date(command.periodo_inicio or plan.periodo.inicio)
            fin = coerce_date(command.periodo_fin or plan.periodo.fin)
            plan.periodo = DateRange(inicio, fin)
        if command.budget_amount is not None or command.budget_currency is not None:
            amount = (
                coerce_decimal(command.budget_amount)
                if command.budget_amount is not None
                else plan.budget.amount
            )
            currency = (
                command.budget_currency.strip().upper()
                if command.budget_currency is not None
                else plan.budget.currency
            )
            plan.budget = Budget(amount, currency)
        if command.prioridad is not None:
            plan.prioridad = parse_plan_priority(command.prioridad)
        if command.observaciones is not None:
            plan.observaciones = command.observaciones

        plan.updated_at = self._clock.now()
        validate_plan_fields(plan)
        self._repository.save(plan)
        return MutationResult(plan=plan.copy(), events=[])

    def activate_plan(self, command: ActivatePlanCommand) -> MutationResult:
        plan = self._require_plan(command.plan_id, command.tenant_id)
        if plan.estado == PlanStatus.FINALIZADO:
            raise DomainError(
                DomainErrorCode.PLAN_COMPLETED,
                "Un plan finalizado no puede activarse",
                {"plan_id": plan.id},
            )
        if plan.estado == PlanStatus.ACTIVO:
            return MutationResult(plan=plan.copy(), events=[])

        self._ensure_transition(plan.estado, PlanStatus.ACTIVO)

        events: list[DomainEvent] = []
        previous_active = self._repository.find_active(plan.tenant_id, plan.app_id)
        resolution_event: str | None = None

        if previous_active and previous_active.id != plan.id:
            if command.resolution is None:
                raise DomainError(
                    DomainErrorCode.ACTIVE_PLAN_RESOLUTION_REQUIRED,
                    "Existe otro plan activo; se requiere resolución R2",
                    {
                        "active_plan_id": previous_active.id,
                        "requested_plan_id": plan.id,
                    },
                )
            if command.resolution == ConflictResolution.FINALIZE_PREVIOUS:
                prev_result = self._complete_plan_internal(
                    previous_active,
                    command.activated_by,
                )
                events.extend(prev_result.events)
            elif command.resolution == ConflictResolution.PAUSE_PREVIOUS:
                prev_result = self._pause_plan_internal(
                    previous_active,
                    command.activated_by,
                )
                events.extend(prev_result.events)
            resolution_event = RESOLUTION_TO_EVENT[command.resolution]

        now = self._clock.now()
        plan.estado = PlanStatus.ACTIVO
        plan.activated_at = now
        plan.updated_at = now
        validate_plan_fields(plan)
        self._repository.save(plan)

        events.append(
            PlanActivated(
                event_id=self._ids.new_event_id(),
                occurred_at=now,
                plan_id=plan.id,
                tenant_id=plan.tenant_id,
                app_id=plan.app_id,
                previous_active_plan_id=previous_active.id if previous_active else None,
                resolution=resolution_event,
                activated_by=command.activated_by.strip(),
            )
        )
        return MutationResult(plan=plan.copy(), events=events)

    def pause_plan(self, command: PausePlanCommand) -> MutationResult:
        plan = self._require_plan(command.plan_id, command.tenant_id)
        if plan.estado == PlanStatus.PAUSADO:
            return MutationResult(plan=plan.copy(), events=[])
        if plan.estado == PlanStatus.FINALIZADO:
            raise DomainError(
                DomainErrorCode.PLAN_COMPLETED,
                "Un plan finalizado no puede pausarse",
                {"plan_id": plan.id},
            )
        return self._pause_plan_internal(plan, command.paused_by)

    def complete_plan(self, command: CompletePlanCommand) -> MutationResult:
        plan = self._require_plan(command.plan_id, command.tenant_id)
        if plan.estado == PlanStatus.FINALIZADO:
            return MutationResult(plan=plan.copy(), events=[])
        return self._complete_plan_internal(plan, command.completed_by)

    def get_plan(self, plan_id: str, tenant_id: str) -> MarketingPlan:
        return self._require_plan(plan_id, tenant_id).copy()

    def get_active_plan(self, tenant_id: str, app_id: str) -> MarketingPlan | None:
        plan = self._repository.find_active(tenant_id, app_id)
        return plan.copy() if plan else None

    def list_plans(
        self,
        tenant_id: str,
        *,
        app_id: str | None = None,
        estado: PlanStatus | None = None,
    ) -> list[MarketingPlan]:
        return self._repository.list_plans(tenant_id, app_id=app_id, estado=estado)

    def _pause_plan_internal(self, plan: MarketingPlan, actor: str) -> MutationResult:
        self._ensure_transition(plan.estado, PlanStatus.PAUSADO)
        now = self._clock.now()
        plan.estado = PlanStatus.PAUSADO
        plan.updated_at = now
        validate_plan_fields(plan)
        self._repository.save(plan)
        event = PlanPaused(
            event_id=self._ids.new_event_id(),
            occurred_at=now,
            plan_id=plan.id,
            tenant_id=plan.tenant_id,
            app_id=plan.app_id,
            paused_by=actor.strip(),
        )
        return MutationResult(plan=plan.copy(), events=[event])

    def _complete_plan_internal(self, plan: MarketingPlan, actor: str) -> MutationResult:
        self._ensure_transition(plan.estado, PlanStatus.FINALIZADO)
        now = self._clock.now()
        plan.estado = PlanStatus.FINALIZADO
        plan.updated_at = now
        validate_plan_fields(plan)
        self._repository.save(plan)
        event = PlanCompleted(
            event_id=self._ids.new_event_id(),
            occurred_at=now,
            plan_id=plan.id,
            tenant_id=plan.tenant_id,
            app_id=plan.app_id,
            completed_by=actor.strip(),
        )
        return MutationResult(plan=plan.copy(), events=[event])

    def _require_plan(self, plan_id: str, tenant_id: str) -> MarketingPlan:
        plan = self._repository.get_by_id(plan_id)
        if plan is None or plan.tenant_id != tenant_id:
            raise DomainError(
                DomainErrorCode.PLAN_NOT_FOUND,
                f"Plan no encontrado: {plan_id}",
                {"plan_id": plan_id, "tenant_id": tenant_id},
            )
        return plan

    def _ensure_transition(self, current: PlanStatus, target: PlanStatus) -> None:
        allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise DomainError(
                DomainErrorCode.INVALID_STATUS_TRANSITION,
                f"Transición no permitida: {current.value} → {target.value}",
                {"from": current.value, "to": target.value},
            )

    def _ensure_tenant_app(self, tenant_id: str, app_id: str) -> None:
        if not tenant_id.strip():
            raise DomainError(DomainErrorCode.TENANT_REQUIRED, "tenant_id es obligatorio")
        if not app_id.strip():
            raise DomainError(DomainErrorCode.APP_REQUIRED, "app_id es obligatorio")
        if not self._tenant_apps.tenant_exists(tenant_id):
            raise DomainError(
                DomainErrorCode.TENANT_NOT_FOUND,
                f"Tenant no encontrado: {tenant_id}",
            )
        if not self._tenant_apps.app_exists(tenant_id, app_id):
            raise DomainError(
                DomainErrorCode.APP_NOT_FOUND,
                f"App no encontrada: {app_id}",
                {"tenant_id": tenant_id, "app_id": app_id},
            )
