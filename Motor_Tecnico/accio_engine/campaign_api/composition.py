from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.campaign_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.campaign_application.engine_use_cases import (
    ApproveCampaign,
    ArchiveCampaign,
    CreateCampaignFromRecommendation,
    EnrichCampaign,
    GetCampaignExplain,
    GetEngineCampaign,
    ListEngineCampaigns,
    PatchCampaign,
)
from Motor_Tecnico.accio_engine.campaign_application.use_cases import GetCampaign, ListCampaigns
from Motor_Tecnico.accio_engine.campaign_domain.engine_service import CampaignEngineService
from Motor_Tecnico.accio_engine.campaign_domain.service import CampaignDomainService
from Motor_Tecnico.accio_engine.campaign_infrastructure.application_adapters import CampaignRbacAdapter
from Motor_Tecnico.accio_engine.campaign_infrastructure.composite_repository import CompositeCampaignRepository
from Motor_Tecnico.accio_engine.campaign_infrastructure.engine_orchestrator import CampaignEngineOrchestrator
from Motor_Tecnico.accio_engine.campaign_infrastructure.engine_sqlite_repository import SqliteCampaignEngineRepository
from Motor_Tecnico.accio_engine.decision_engine_api.composition import build_recommendation_service
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.opportunity_api.composition import build_opportunity_detector
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_campaign_domain_service() -> CampaignDomainService:
    ensure_schema()
    return CampaignDomainService(CompositeCampaignRepository())


def build_campaign_engine_service() -> CampaignEngineService:
    ensure_schema()
    return CampaignEngineService(SqliteCampaignEngineRepository())


def build_campaign_orchestrator() -> CampaignEngineOrchestrator:
    return CampaignEngineOrchestrator(
        build_campaign_engine_service(),
        build_recommendation_service(),
        build_opportunity_detector(),
    )


class CampaignUseCases:
    def __init__(self) -> None:
        campaigns = build_campaign_domain_service()
        auth = CampaignRbacAdapter()
        self.list_campaigns = ListCampaigns(campaigns, auth)
        self.get_campaign = GetCampaign(campaigns, auth)


class CampaignEngineUseCases:
    def __init__(self) -> None:
        engine = build_campaign_engine_service()
        orchestrator = build_campaign_orchestrator()
        auth = CampaignRbacAdapter()
        self.list_campaigns = ListEngineCampaigns(engine, auth)
        self.get_campaign = GetEngineCampaign(engine, auth)
        self.from_recommendation = CreateCampaignFromRecommendation(orchestrator, auth)
        self.enrich_campaign = EnrichCampaign(orchestrator, auth)
        self.patch_campaign = PatchCampaign(engine, auth)
        self.approve_campaign = ApproveCampaign(engine, auth)
        self.archive_campaign = ArchiveCampaign(engine, auth)
        self.get_explain = GetCampaignExplain(engine, auth)


_USE_CASES: CampaignUseCases | None = None
_ENGINE_USE_CASES: CampaignEngineUseCases | None = None


def campaign_use_cases() -> CampaignUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = CampaignUseCases()
    return _USE_CASES


def campaign_engine_use_cases() -> CampaignEngineUseCases:
    global _ENGINE_USE_CASES
    if _ENGINE_USE_CASES is None:
        _ENGINE_USE_CASES = CampaignEngineUseCases()
    return _ENGINE_USE_CASES


def reset_campaign_use_cases() -> None:
    global _USE_CASES, _ENGINE_USE_CASES
    _USE_CASES = None
    _ENGINE_USE_CASES = None


def tenant_app_context(tenant_id: str, app_id: str) -> TenantAppContext:
    return TenantAppContext(
        tenant_id=tenant_id,
        app_id=marketing_app.normalize_app_id(app_id),
    )


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
