from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.brand_infrastructure.facade import get_brand_service
from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import get_company_brain_service
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot
from Motor_Tecnico.accio_engine.lead_infrastructure.facade import get_lead_service
from Motor_Tecnico.accio_engine.publication_infrastructure.facade import get_publication_service


class CompositeKnowledgeReader:
    """Composes KnowledgeSnapshot from M2–M4 and M9 repositories."""

    def read(self, tenant_id: str) -> KnowledgeSnapshot:
        brands = get_brand_service().list_brands(tenant_id, active_only=True)
        publication_service = get_publication_service()
        pubs_by_brand: dict[str, tuple] = {}
        for brand in brands:
            brand_id = brand.legacy_app_id
            rows = publication_service.list_publications(tenant_id, brand_id)
            pubs_by_brand[brand_id] = tuple(rows)

        leads_by_brand: dict[str, list] = {}
        for lead in get_lead_service().list_leads(tenant_id, limit=500):
            key = lead.brand_id or "default"
            leads_by_brand.setdefault(key, []).append(lead)
        leads_tuple = {key: tuple(rows) for key, rows in leads_by_brand.items()}

        brain = get_company_brain_service().get_or_empty(tenant_id)
        return KnowledgeSnapshot(
            tenant_id=tenant_id,
            company_id=tenant_id,
            generated_at=KnowledgeSnapshot.now_iso(),
            brands=tuple(brands),
            publications_by_brand=pubs_by_brand,
            company_brain=brain,
            leads_by_brand=leads_tuple,
        )
