from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_infrastructure.facade import get_brand_service
from Motor_Tecnico.accio_engine.campaign_infrastructure.facade import get_campaign_service
from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import get_company_brain_service
from Motor_Tecnico.accio_engine.lead_infrastructure.facade import get_lead_service
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot
from Motor_Tecnico.accio_engine.publication_infrastructure.facade import get_publication_service


class CompositeOpportunityKnowledgeReader:
    """Composes OpportunitySnapshot from M2–M9 repositories."""

    def read(self, tenant_id: str) -> OpportunitySnapshot:
        brands = get_brand_service().list_brands(tenant_id, active_only=True)
        publication_service = get_publication_service()
        campaign_service = get_campaign_service()

        pubs_by_brand: dict[str, tuple] = {}
        campaigns_by_brand: dict[str, tuple] = {}
        for brand in brands:
            brand_id = brand.legacy_app_id or brand.brand_id
            pubs_by_brand[brand_id] = tuple(publication_service.list_publications(tenant_id, brand_id))
            try:
                campaigns_by_brand[brand_id] = tuple(campaign_service.list_campaigns(tenant_id, brand_id))
            except (KeyError, FileNotFoundError):
                campaigns_by_brand[brand_id] = ()

        leads_by_brand: dict[str, list] = {}
        for lead in get_lead_service().list_leads(tenant_id, limit=500):
            key = lead.brand_id or "default"
            leads_by_brand.setdefault(key, []).append(lead)

        brain = get_company_brain_service().get_or_empty(tenant_id)
        return OpportunitySnapshot(
            tenant_id=tenant_id,
            company_id=tenant_id,
            generated_at=OpportunitySnapshot.now_iso(),
            brands=tuple(brands),
            publications_by_brand=pubs_by_brand,
            campaigns_by_brand=campaigns_by_brand,
            leads_by_brand={key: tuple(rows) for key, rows in leads_by_brand.items()},
            company_brain=brain,
        )
