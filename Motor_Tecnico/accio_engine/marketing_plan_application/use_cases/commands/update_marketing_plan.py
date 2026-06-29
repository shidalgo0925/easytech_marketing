from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application._authorization_helpers import require_config_or_admin
from Motor_Tecnico.accio_engine.marketing_plan_application.command_inputs import UpdateMarketingPlanInput
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import (
    AuthorizationPort,
    DomainEventPublisher,
    TenantAppContextPort,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.results import CommandResult
from Motor_Tecnico.accio_engine.marketing_plan_domain.commands import UpdatePlanCommand
from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import DomainError
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService


class UpdateMarketingPlan:
    def __init__(
        self,
        domain: MarketingPlanDomainService,
        authorization: AuthorizationPort,
        workspace: TenantAppContextPort,
        events: DomainEventPublisher,
    ) -> None:
        self._domain = domain
        self._authorization = authorization
        self._workspace = workspace
        self._events = events

    def __call__(self, ctx: ApplicationContext, data: UpdateMarketingPlanInput) -> CommandResult:
        require_config_or_admin(ctx, self._authorization)
        self._workspace.ensure_workspace(ctx)
        command = UpdatePlanCommand(
            plan_id=data.plan_id,
            tenant_id=ctx.tenant_id,
            updated_by=ctx.actor_id,
            nombre=data.nombre,
            objetivo_general=data.objetivo_general,
            strategy_type=data.strategy_type,
            north_star_metric=data.north_star_metric,
            success_criteria=data.success_criteria,
            publico_objetivo=data.publico_objetivo,
            marketing_brief=data.marketing_brief,
            periodo_inicio=data.periodo_inicio,
            periodo_fin=data.periodo_fin,
            budget_amount=data.budget_amount,
            budget_currency=data.budget_currency,
            prioridad=data.prioridad,
            observaciones=data.observaciones,
            extra_fields=data.extra_fields,
        )
        try:
            result = self._domain.update_plan(command)
        except DomainError as exc:
            raise ApplicationError.from_domain(exc) from exc
        self._events.publish(result.events)
        return CommandResult(plan=result.plan, events=result.events)
