from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application._authorization_helpers import require_admin
from Motor_Tecnico.accio_engine.marketing_plan_application.command_inputs import PauseMarketingPlanInput
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import (
    AuthorizationPort,
    DomainEventPublisher,
    TenantAppContextPort,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.results import CommandResult
from Motor_Tecnico.accio_engine.marketing_plan_domain.commands import PausePlanCommand
from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import DomainError
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService


class PauseMarketingPlan:
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

    def __call__(self, ctx: ApplicationContext, data: PauseMarketingPlanInput) -> CommandResult:
        require_admin(ctx, self._authorization)
        self._workspace.ensure_workspace(ctx)
        command = PausePlanCommand(
            plan_id=data.plan_id,
            tenant_id=ctx.tenant_id,
            paused_by=ctx.actor_id,
        )
        try:
            result = self._domain.pause_plan(command)
        except DomainError as exc:
            raise ApplicationError.from_domain(exc) from exc
        self._events.publish(result.events)
        return CommandResult(plan=result.plan, events=result.events)
