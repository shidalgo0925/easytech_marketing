"""Facade for dashboard_data, publications_api and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.platform_infrastructure.db import campaign_sql_enabled
from Motor_Tecnico.accio_engine.campaign_domain.service import CampaignDomainService
from Motor_Tecnico.accio_engine.campaign_infrastructure.composite_repository import CompositeCampaignRepository

_SERVICE: CampaignDomainService | None = None


def get_campaign_service() -> CampaignDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CampaignDomainService(CompositeCampaignRepository())
    return _SERVICE


def reset_campaign_service() -> None:
    global _SERVICE
    _SERVICE = None


def _resolve_brand_id(tenant_id: str, app_id: str | None) -> str:
    return marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))


def campaign_store_active() -> bool:
    return campaign_sql_enabled()


def load_campaigns_store(tenant_id: str, app_id: str | None = None) -> dict:
    brand_id = _resolve_brand_id(tenant_id, app_id)
    return get_campaign_service().load_store(tenant_id, brand_id)


def campaign_defs_by_post_id(tenant_id: str, app_id: str | None = None) -> dict[str, dict]:
    data = load_campaigns_store(tenant_id, app_id)
    defs: dict[str, dict] = {}
    for camp in data.get("campaigns", []):
        post_id = camp.get("post_id")
        if post_id:
            defs[post_id] = camp
    return defs


def campaign_id_for_post(tenant_id: str, app_id: str, post_id: str) -> str:
    camp = campaign_defs_by_post_id(tenant_id, app_id).get(post_id, {})
    return camp.get("id") or camp.get("product") or ""


def list_campaigns(tenant_id: str, app_id: str | None = None) -> list[dict]:
    brand_id = _resolve_brand_id(tenant_id, app_id)
    return [c.to_api_dict() for c in get_campaign_service().list_campaigns(tenant_id, brand_id)]
