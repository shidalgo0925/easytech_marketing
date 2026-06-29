"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import lead_json_enabled, lead_sql_enabled
from Motor_Tecnico.accio_engine.lead_domain.model import Lead
from Motor_Tecnico.accio_engine.lead_domain.ports import LeadRepository

from .json_repository import JsonLeadRepository
from .sqlite_repository import SqliteLeadRepository


class CompositeLeadRepository:
    def __init__(
        self,
        json_repo: LeadRepository | None = None,
        sql_repo: LeadRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonLeadRepository()
        self._sql = sql_repo or SqliteLeadRepository()

    def load_catalog(self, tenant_id: str) -> dict:
        if lead_sql_enabled():
            data = self._sql.load_catalog(tenant_id)
            if data.get("leads"):
                return data
        if lead_json_enabled():
            return self._json.load_catalog(tenant_id)
        return {"version": 1, "leads": []}

    def save_catalog(self, tenant_id: str, data: dict) -> None:
        if lead_sql_enabled():
            self._sql.save_catalog(tenant_id, data)
        if lead_json_enabled():
            self._json.save_catalog(tenant_id, data)

    def list_leads(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Lead]:
        if lead_sql_enabled():
            rows = self._sql.list_leads(tenant_id, brand_id=brand_id, limit=limit)
            if rows:
                return rows
        if lead_json_enabled():
            return self._json.list_leads(tenant_id, brand_id=brand_id, limit=limit)
        return []

    def get_lead(self, tenant_id: str, lead_id: str) -> Lead | None:
        if lead_sql_enabled():
            row = self._sql.get_lead(tenant_id, lead_id)
            if row is not None:
                return row
        if lead_json_enabled():
            return self._json.get_lead(tenant_id, lead_id)
        return None

    def append_lead(self, tenant_id: str, entry: dict) -> Lead:
        lead: Lead | None = None
        if lead_sql_enabled():
            lead = self._sql.append_lead(tenant_id, entry)
        if lead_json_enabled():
            lead = self._json.append_lead(tenant_id, entry)
        if lead is None:
            raise RuntimeError("No lead store enabled")
        return lead
