from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application._authorization_helpers import require_read
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import AuthorizationPort, TenantAppContextPort
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import GetActiveMarketingPlanQuery
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService


class GetActiveMarketingPlan:
    def __init__(
        self,
        domain: MarketingPlanDomainService,
        authorization: AuthorizationPort,
        workspace: TenantAppContextPort,
    ) -> None:
        self._domain = domain
        self._authorization = authorization
        self._workspace = workspace

    def __call__(
        self,
        ctx: ApplicationContext,
        query: GetActiveMarketingPlanQuery | None = None,
    ) -> MarketingPlan | None:
        require_read(ctx, self._authorization)
        self._workspace.ensure_workspace(ctx)
        return self._domain.get_active_plan(ctx.tenant_id, ctx.app_id)
