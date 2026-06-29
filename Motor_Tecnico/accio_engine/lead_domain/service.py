from __future__ import annotations

from Motor_Tecnico.accio_engine.lead_domain.errors import LeadNotFound
from Motor_Tecnico.accio_engine.lead_domain.model import Lead
from Motor_Tecnico.accio_engine.lead_domain.ports import LeadRepository


class LeadDomainService:
    def __init__(self, repository: LeadRepository) -> None:
        self._repo = repository

    def load_catalog(self, tenant_id: str) -> dict:
        return self._repo.load_catalog(tenant_id)

    def save_catalog(self, tenant_id: str, data: dict) -> None:
        self._repo.save_catalog(tenant_id, data)

    def list_leads(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        return self._repo.list_leads(tenant_id, brand_id=brand_id, limit=limit)

    def get_lead(self, tenant_id: str, lead_id: str) -> Lead:
        row = self._repo.get_lead(tenant_id, lead_id)
        if row is None:
            raise LeadNotFound(f"Lead no encontrado: {lead_id}")
        return row

    def append_lead(self, tenant_id: str, entry: dict) -> Lead:
        return self._repo.append_lead(tenant_id, entry)
