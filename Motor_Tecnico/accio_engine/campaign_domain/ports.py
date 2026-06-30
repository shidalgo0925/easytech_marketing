from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign


class CampaignRepository(Protocol):
    def load_store(self, tenant_id: str, brand_id: str) -> dict:
        ...

    def save_store(self, tenant_id: str, brand_id: str, data: dict) -> dict:
        ...

    def list_campaigns(self, tenant_id: str, brand_id: str) -> list[Campaign]:
        ...

    def get_campaign(self, tenant_id: str, brand_id: str, campaign_id: str) -> Campaign | None:
        ...


class CampaignEngineRepository(Protocol):
    def save(self, campaign: Campaign) -> Campaign:
        ...

    def get(self, tenant_id: str, campaign_id: str) -> Campaign | None:
        ...

    def list_campaigns(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Campaign]:
        ...

    def append_history(
        self,
        tenant_id: str,
        campaign_id: str,
        event_type: str,
        *,
        actor_id: str = "system",
        payload: dict | None = None,
    ) -> None:
        ...
