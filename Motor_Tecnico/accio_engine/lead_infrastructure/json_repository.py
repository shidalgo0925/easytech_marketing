"""JSON adapter — leads.json per tenant."""

from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine.lead_domain.model import Lead
from Motor_Tecnico.accio_engine.lead_infrastructure.legacy_mapper import catalog_to_leads, legacy_row_to_lead, leads_to_catalog
from Motor_Tecnico.accio_engine.tenant import resolve_tenant


class JsonLeadRepository:
    def _path(self, tenant_id: str) -> Path:
        return resolve_tenant(tenant_id).root / "leads.json"

    def _read_raw(self, tenant_id: str) -> dict:
        path = self._path(tenant_id)
        if not path.is_file():
            return {"version": 1, "leads": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_catalog(self, tenant_id: str) -> dict:
        return self._read_raw(tenant_id)

    def save_catalog(self, tenant_id: str, data: dict) -> None:
        path = self._path(tenant_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def list_leads(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        items = catalog_to_leads(tenant_id, self._read_raw(tenant_id))
        if brand_id:
            items = [x for x in items if x.brand_id == brand_id]
        items.sort(key=lambda x: x.created_at or "", reverse=True)
        return items[:limit]

    def get_lead(self, tenant_id: str, lead_id: str) -> Lead | None:
        for lead in catalog_to_leads(tenant_id, self._read_raw(tenant_id)):
            if lead.lead_id == lead_id:
                return lead
        return None

    def append_lead(self, tenant_id: str, entry: dict) -> Lead:
        data = self._read_raw(tenant_id)
        data.setdefault("leads", []).append(entry)
        self.save_catalog(tenant_id, data)
        return legacy_row_to_lead(tenant_id, entry)
