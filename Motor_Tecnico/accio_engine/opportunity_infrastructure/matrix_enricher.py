"""Enrich opportunity candidates with product-sector matrix."""

from __future__ import annotations

from dataclasses import replace

from Motor_Tecnico.accio_engine.knowledge_matrix_api.composition import get_knowledge_matrix_service
from Motor_Tecnico.accio_engine.opportunity_domain.model import OpportunityCandidate


def enrich_opportunity_candidate(tenant_id: str, candidate: OpportunityCandidate) -> OpportunityCandidate:
    matrix = get_knowledge_matrix_service()
    text = f"{candidate.title} {candidate.description} {candidate.need}"
    classification = matrix.resolve_product(tenant_id, brand_id=candidate.brand_id, text=text)
    payload = dict(candidate.payload or {})
    payload["matrix"] = classification.to_dict()
    return replace(
        candidate,
        sector=classification.sector_label,
        need=classification.need or candidate.need,
        product_slug=classification.product_slug,
        landing_url=classification.landing_url,
        confidence=max(candidate.confidence, classification.confidence),
        payload=payload,
    )
