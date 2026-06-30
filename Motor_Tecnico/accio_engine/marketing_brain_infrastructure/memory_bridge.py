"""Record Marketing Brain events in Corporate Memory."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap, Recommendation
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment
from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


def record_recommendation_enriched(
    memory: CorporateMemoryDomainService | None,
    *,
    recommendation: Recommendation,
    enrichment: RecommendationEnrichment,
    actor_id: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=recommendation.tenant_id,
            brand_id=recommendation.brand_id,
            event_type="RecommendationEnriched",
            actor=Actor(type="user" if actor_id != "system" else "system", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Recommendation", id=recommendation.recommendation_id),
                EntityRef(type="Brand", id=recommendation.brand_id),
            ),
            payload={
                "title": recommendation.title,
                "action": recommendation.action,
                "model": enrichment.model,
                "confidence": enrichment.confidence,
                "reason": enrichment.reason[:500],
            },
            summary=f"Recomendación enriquecida por IA: {recommendation.title}",
        )
    )


def record_daily_roadmap_enriched(
    memory: CorporateMemoryDomainService | None,
    *,
    roadmap: DailyRoadmap,
    ai_summary: dict[str, Any],
    actor_id: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=roadmap.tenant_id,
            event_type="DailyRoadmapEnriched",
            actor=Actor(type="user" if actor_id != "system" else "system", id=actor_id),
            timestamp="",
            entity_refs=(EntityRef(type="DailyRoadmap", id=roadmap.roadmap_id),),
            payload={
                "roadmap_date": roadmap.roadmap_date,
                "ai_enrichment": ai_summary,
            },
            summary=(
                f"Roadmap enriquecido por IA: {roadmap.roadmap_date} "
                f"({ai_summary.get('enriched_count', 0)} recomendaciones)"
            ),
        )
    )
