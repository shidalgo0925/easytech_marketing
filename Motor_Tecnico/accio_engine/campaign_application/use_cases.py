from __future__ import annotations

from Motor_Tecnico.accio_engine.campaign_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.campaign_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.campaign_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_domain.service import CampaignDomainService


class ListCampaigns:
    def __init__(self, campaigns: CampaignDomainService, authorization: AuthorizationPort) -> None:
        self._campaigns = campaigns
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext) -> list[Campaign]:
        self._authorization.require_permission(ctx, "read")
        return self._campaigns.list_campaigns(ctx.tenant_id, ctx.app_id)


class GetCampaign:
    def __init__(self, campaigns: CampaignDomainService, authorization: AuthorizationPort) -> None:
        self._campaigns = campaigns
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext, campaign_id: str) -> Campaign:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._campaigns.get_campaign(ctx.tenant_id, ctx.app_id, campaign_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc
