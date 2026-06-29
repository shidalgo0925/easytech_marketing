"""JSON adapter — campaigns.json per app."""

from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_infrastructure.legacy_mapper import (
    campaigns_to_store,
    store_to_campaigns,
)


class JsonCampaignRepository:
    def _path(self, tenant_id: str, brand_id: str) -> Path:
        aid = marketing_app.normalize_app_id(brand_id)
        if aid == marketing_app.default_app_id(tenant_id):
            from Motor_Tecnico.accio_engine.tenant import resolve_tenant

            return resolve_tenant(tenant_id).root / "campaigns.json"
        return marketing_app.effective_app_paths(tenant_id, aid)["campaigns"]

    def _read_raw(self, tenant_id: str, brand_id: str) -> dict:
        path = self._path(tenant_id, brand_id)
        if not path.is_file():
            return {"campaigns": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_store(self, tenant_id: str, brand_id: str) -> dict:
        return self._read_raw(tenant_id, brand_id)

    def save_store(self, tenant_id: str, brand_id: str, data: dict) -> dict:
        path = self._path(tenant_id, brand_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return data

    def list_campaigns(self, tenant_id: str, brand_id: str) -> list[Campaign]:
        return store_to_campaigns(tenant_id, brand_id, self._read_raw(tenant_id, brand_id))

    def get_campaign(self, tenant_id: str, brand_id: str, campaign_id: str) -> Campaign | None:
        for campaign in self.list_campaigns(tenant_id, brand_id):
            if campaign.campaign_id == campaign_id:
                return campaign
        return None
