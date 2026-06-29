from __future__ import annotations

from Motor_Tecnico.accio_engine.lead_application.context import TenantContext
from Motor_Tecnico.accio_engine.lead_application.use_cases import GetLead, ListLeads
from Motor_Tecnico.accio_engine.lead_domain.service import LeadDomainService
from Motor_Tecnico.accio_engine.lead_infrastructure.application_adapters import LeadRbacAdapter
from Motor_Tecnico.accio_engine.lead_infrastructure.composite_repository import CompositeLeadRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_lead_domain_service() -> LeadDomainService:
    ensure_schema()
    return LeadDomainService(CompositeLeadRepository())


class LeadUseCases:
    def __init__(self) -> None:
        leads = build_lead_domain_service()
        auth = LeadRbacAdapter()
        self.list_leads = ListLeads(leads, auth)
        self.get_lead = GetLead(leads, auth)


_USE_CASES: LeadUseCases | None = None


def lead_use_cases() -> LeadUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = LeadUseCases()
    return _USE_CASES


def reset_lead_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
