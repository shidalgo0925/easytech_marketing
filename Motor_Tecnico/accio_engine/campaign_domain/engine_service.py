from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError, CampaignNotFound
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_domain.ports import CampaignEngineRepository
from Motor_Tecnico.accio_engine.campaign_domain.constants import ENGINE_CAMPAIGN_STATUSES


class CampaignInvalidStatus(CampaignError):
    code = "campaign_invalid_status"


class CampaignEngineService:
    APPROVABLE = frozenset({"draft", "pending_approval"})
    ARCHIVABLE = frozenset({"draft", "pending_approval", "approved", "scheduled", "running", "completed", "cancelled"})

    def __init__(self, repository: CampaignEngineRepository) -> None:
        self._repo = repository

    def save(self, campaign: Campaign) -> Campaign:
        return self._repo.save(campaign)

    def get(self, tenant_id: str, campaign_id: str) -> Campaign:
        row = self._repo.get(tenant_id, campaign_id)
        if row is None:
            raise CampaignNotFound(f"Campaña no encontrada: {campaign_id}")
        return row

    def list_campaigns(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Campaign]:
        return self._repo.list_campaigns(tenant_id, status=status, brand_id=brand_id, limit=limit)

    def update_fields(self, tenant_id: str, campaign_id: str, **fields: Any) -> Campaign:
        from dataclasses import replace

        row = self.get(tenant_id, campaign_id)
        allowed = {
            "name",
            "description",
            "objective",
            "target_audience",
            "value_proposition",
            "call_to_action",
            "priority",
            "owner",
            "start_date",
            "end_date",
            "budget",
            "status",
            "explain",
            "llm_enrichment",
            "llm_skipped",
        }
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if "status" in updates and updates["status"] not in ENGINE_CAMPAIGN_STATUSES | {"active"}:
            raise CampaignInvalidStatus(f"Estado no válido: {updates['status']}")
        updated = replace(row, **updates, updated_at=_utc_now())
        if "start_date" in updates:
            updated = replace(updated, start_at=updates["start_date"])
        if "end_date" in updates:
            updated = replace(updated, end_at=updates["end_date"])
        return self._repo.save(updated)

    def approve(self, tenant_id: str, campaign_id: str, *, actor_id: str = "system") -> Campaign:
        row = self.get(tenant_id, campaign_id)
        if row.status not in self.APPROVABLE:
            raise CampaignInvalidStatus(f"No se puede aprobar campaña en estado {row.status}")
        from dataclasses import replace

        updated = replace(row, status="approved", updated_at=_utc_now())
        saved = self._repo.save(updated)
        self._repo.append_history(tenant_id, campaign_id, "approved", actor_id=actor_id)
        return saved

    def archive(self, tenant_id: str, campaign_id: str, *, actor_id: str = "system") -> Campaign:
        row = self.get(tenant_id, campaign_id)
        if row.status not in self.ARCHIVABLE:
            raise CampaignInvalidStatus(f"No se puede archivar campaña en estado {row.status}")
        from dataclasses import replace

        updated = replace(row, status="archived", updated_at=_utc_now())
        saved = self._repo.save(updated)
        self._repo.append_history(tenant_id, campaign_id, "archived", actor_id=actor_id)
        return saved

    def record_created(self, campaign: Campaign, *, actor_id: str = "system") -> None:
        self._repo.append_history(
            campaign.tenant_id,
            campaign.campaign_id,
            "created",
            actor_id=actor_id,
            payload={"recommendation_id": campaign.recommendation_id},
        )

    def record_enriched(self, campaign: Campaign, *, actor_id: str = "system", skipped: bool = False) -> None:
        self._repo.append_history(
            campaign.tenant_id,
            campaign.campaign_id,
            "enriched" if not skipped else "enrich_skipped",
            actor_id=actor_id,
            payload={"llm_skipped": skipped},
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_history_id() -> str:
    return f"ch_{secrets.token_hex(6)}"
