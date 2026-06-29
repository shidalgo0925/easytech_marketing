from __future__ import annotations

from Motor_Tecnico.accio_engine.marketing_plan_application._authorization_helpers import require_read
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext
from Motor_Tecnico.accio_engine.marketing_plan_application.ports import AuthorizationPort, TenantAppContextPort
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import ListMarketingPlansQuery
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService


class ListMarketingPlans:
    def __init__(
        self,
        domain: MarketingPlanDomainService,
        authorization: AuthorizationPort,
        workspace: TenantAppContextPort,
    ) -> None:
        self._domain = domain
        self._authorization = authorization
        self._workspace = workspace

    def __call__(self, ctx: ApplicationContext, query: ListMarketingPlansQuery) -> list[MarketingPlan]:
        require_read(ctx, self._authorization)
        self._workspace.ensure_workspace(ctx)
        app_id = query.app_id if query.app_id is not None else ctx.app_id
        return self._domain.list_plans(ctx.tenant_id, app_id=app_id, estado=query.estado)
