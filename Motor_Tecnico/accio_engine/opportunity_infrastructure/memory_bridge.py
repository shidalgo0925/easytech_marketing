"""Record Opportunity Engine events in Corporate Memory."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity


def record_opportunity_identified(
    memory: CorporateMemoryDomainService | None,
    *,
    opportunity: Opportunity,
    actor_id: str = "system",
    created: bool = True,
) -> None:
    if memory is None or not created:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=opportunity.tenant_id,
            brand_id=opportunity.brand_id or None,
            event_type="OpportunityIdentified",
            actor=Actor(type="system" if actor_id == "system" else "user", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Opportunity", id=opportunity.opportunity_id),
                EntityRef(type="Brand", id=opportunity.brand_id),
            ),
            payload={
                "signal_type": opportunity.signal_type,
                "signal_key": opportunity.signal_key,
                "product_slug": opportunity.product_slug,
                "priority": opportunity.priority,
                "sector": opportunity.sector,
            },
            summary=f"Oportunidad detectada: {opportunity.title}",
        )
    )


def record_opportunity_promoted(
    memory: CorporateMemoryDomainService | None,
    *,
    opportunity: Opportunity,
    recommendation_id: str,
    actor_id: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=opportunity.tenant_id,
            brand_id=opportunity.brand_id or None,
            event_type="OpportunityPromoted",
            actor=Actor(type="user" if actor_id != "system" else "system", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Opportunity", id=opportunity.opportunity_id),
                EntityRef(type="Recommendation", id=recommendation_id),
                EntityRef(type="Brand", id=opportunity.brand_id),
            ),
            payload={
                "signal_type": opportunity.signal_type,
                "recommendation_id": recommendation_id,
            },
            summary=f"Oportunidad promovida a recomendación: {opportunity.title}",
        )
    )


def record_opportunity_dismissed(
    memory: CorporateMemoryDomainService | None,
    *,
    opportunity: Opportunity,
    actor_id: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=opportunity.tenant_id,
            brand_id=opportunity.brand_id or None,
            event_type="OpportunityDismissed",
            actor=Actor(type="user" if actor_id != "system" else "system", id=actor_id),
            timestamp="",
            entity_refs=(EntityRef(type="Opportunity", id=opportunity.opportunity_id),),
            payload={"signal_type": opportunity.signal_type},
            summary=f"Oportunidad descartada: {opportunity.title}",
        )
    )
