from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.campaign_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.campaign_application.use_cases import GetCampaign, ListCampaigns
from Motor_Tecnico.accio_engine.campaign_domain.service import CampaignDomainService
from Motor_Tecnico.accio_engine.campaign_infrastructure.application_adapters import CampaignRbacAdapter
from Motor_Tecnico.accio_engine.campaign_infrastructure.composite_repository import CompositeCampaignRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_campaign_domain_service() -> CampaignDomainService:
    ensure_schema()
    return CampaignDomainService(CompositeCampaignRepository())


class CampaignUseCases:
    def __init__(self) -> None:
        campaigns = build_campaign_domain_service()
        auth = CampaignRbacAdapter()
        self.list_campaigns = ListCampaigns(campaigns, auth)
        self.get_campaign = GetCampaign(campaigns, auth)


_USE_CASES: CampaignUseCases | None = None


def campaign_use_cases() -> CampaignUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = CampaignUseCases()
    return _USE_CASES


def reset_campaign_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_app_context(tenant_id: str, app_id: str) -> TenantAppContext:
    return TenantAppContext(
        tenant_id=tenant_id,
        app_id=marketing_app.normalize_app_id(app_id),
    )
