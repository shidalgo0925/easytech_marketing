from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.lead_domain.model import Lead


class LeadRepository(Protocol):
    def load_catalog(self, tenant_id: str) -> dict:
        ...

    def save_catalog(self, tenant_id: str, data: dict) -> None:
        ...

    def list_leads(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        ...

    def get_lead(self, tenant_id: str, lead_id: str) -> Lead | None:
        ...

    def append_lead(self, tenant_id: str, entry: dict) -> Lead:
        ...
