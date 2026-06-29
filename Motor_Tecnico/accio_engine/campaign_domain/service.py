from __future__ import annotations

from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignNotFound
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_domain.ports import CampaignRepository


class CampaignDomainService:
    def __init__(self, repository: CampaignRepository) -> None:
        self._repo = repository

    def load_store(self, tenant_id: str, brand_id: str) -> dict:
        return self._repo.load_store(tenant_id, brand_id)

    def save_store(self, tenant_id: str, brand_id: str, data: dict) -> dict:
        return self._repo.save_store(tenant_id, brand_id, data)

    def list_campaigns(self, tenant_id: str, brand_id: str) -> list[Campaign]:
        return self._repo.list_campaigns(tenant_id, brand_id)

    def get_campaign(self, tenant_id: str, brand_id: str, campaign_id: str) -> Campaign:
        row = self._repo.get_campaign(tenant_id, brand_id, campaign_id)
        if row is None:
            raise CampaignNotFound(f"Campaña no encontrada: {campaign_id}")
        return row
