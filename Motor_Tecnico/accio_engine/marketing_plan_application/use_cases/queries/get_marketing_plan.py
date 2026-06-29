from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application._authorization_helpers import require_read
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import AuthorizationPort, TenantAppContextPort
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import GetMarketingPlanQuery
from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import DomainError
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService


class GetMarketingPlan:
    def __init__(
        self,
        domain: MarketingPlanDomainService,
        authorization: AuthorizationPort,
        workspace: TenantAppContextPort,
    ) -> None:
        self._domain = domain
        self._authorization = authorization
        self._workspace = workspace

    def __call__(self, ctx: ApplicationContext, query: GetMarketingPlanQuery) -> MarketingPlan:
        require_read(ctx, self._authorization)
        self._workspace.ensure_workspace(ctx)
        try:
            return self._domain.get_plan(query.plan_id, ctx.tenant_id)
        except DomainError as exc:
            raise ApplicationError.from_domain(exc) from exc
