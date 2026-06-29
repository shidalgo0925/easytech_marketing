from __future__ import annotations

from Motor_Tecnico.accio_engine.lead_application.context import TenantContext
from Motor_Tecnico.accio_engine.lead_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.lead_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.lead_domain.errors import LeadError
from Motor_Tecnico.accio_engine.lead_domain.model import Lead
from Motor_Tecnico.accio_engine.lead_domain.service import LeadDomainService


class ListLeads:
    def __init__(self, leads: LeadDomainService, authorization: AuthorizationPort) -> None:
        self._leads = leads
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        self._authorization.require_permission(ctx, "read")
        return self._leads.list_leads(ctx.tenant_id, brand_id=brand_id, limit=limit)


class GetLead:
    def __init__(self, leads: LeadDomainService, authorization: AuthorizationPort) -> None:
        self._leads = leads
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, lead_id: str) -> Lead:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._leads.get_lead(ctx.tenant_id, lead_id)
        except LeadError as exc:
            raise ApplicationError.from_domain(exc) from exc
