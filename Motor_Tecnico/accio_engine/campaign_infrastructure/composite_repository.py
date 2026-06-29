"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import campaign_json_enabled, campaign_sql_enabled
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_domain.ports import CampaignRepository

from .json_repository import JsonCampaignRepository
from .sqlite_repository import SqliteCampaignRepository


class CompositeCampaignRepository:
    def __init__(
        self,
        json_repo: CampaignRepository | None = None,
        sql_repo: CampaignRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonCampaignRepository()
        self._sql = sql_repo or SqliteCampaignRepository()

    def load_store(self, tenant_id: str, brand_id: str) -> dict:
        if campaign_sql_enabled():
            data = self._sql.load_store(tenant_id, brand_id)
            if data.get("campaigns"):
                return data
        if campaign_json_enabled():
            return self._json.load_store(tenant_id, brand_id)
        return {"campaigns": []}

    def save_store(self, tenant_id: str, brand_id: str, data: dict) -> dict:
        saved: dict | None = None
        if campaign_sql_enabled():
            saved = self._sql.save_store(tenant_id, brand_id, data)
        if campaign_json_enabled():
            saved = self._json.save_store(tenant_id, brand_id, data)
        return saved or data

    def list_campaigns(self, tenant_id: str, brand_id: str) -> list[Campaign]:
        if campaign_sql_enabled():
            rows = self._sql.list_campaigns(tenant_id, brand_id)
            if rows:
                return rows
        if campaign_json_enabled():
            return self._json.list_campaigns(tenant_id, brand_id)
        return []

    def get_campaign(self, tenant_id: str, brand_id: str, campaign_id: str) -> Campaign | None:
        if campaign_sql_enabled():
            row = self._sql.get_campaign(tenant_id, brand_id, campaign_id)
            if row is not None:
                return row
        if campaign_json_enabled():
            return self._json.get_campaign(tenant_id, brand_id, campaign_id)
        return None
