"""Facade for leads_store and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import lead_sql_enabled
from Motor_Tecnico.accio_engine.lead_domain.service import LeadDomainService
from Motor_Tecnico.accio_engine.lead_infrastructure.composite_repository import CompositeLeadRepository

_SERVICE: LeadDomainService | None = None


def get_lead_service() -> LeadDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = LeadDomainService(CompositeLeadRepository())
    return _SERVICE


def reset_lead_service() -> None:
    global _SERVICE
    _SERVICE = None


def lead_store_active() -> bool:
    return lead_sql_enabled()


def load_leads(tenant_id: str) -> dict:
    return get_lead_service().load_catalog(tenant_id)


def save_leads(data: dict, tenant_id: str) -> None:
    get_lead_service().save_catalog(tenant_id, data)


def list_leads(
    tenant_id: str,
    *,
    app_id: str | None = None,
    limit: int = 50,
) -> list[dict]:
    rows = get_lead_service().list_leads(tenant_id, brand_id=app_id, limit=limit)
    return [lead.to_api_dict() for lead in rows]


def append_lead(tenant_id: str, entry: dict) -> dict:
    lead = get_lead_service().append_lead(tenant_id, entry)
    return lead.to_api_dict()
