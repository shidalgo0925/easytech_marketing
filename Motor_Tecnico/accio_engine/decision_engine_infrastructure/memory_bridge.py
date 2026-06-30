"""Record Decision Engine events in Corporate Memory."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap, Recommendation
from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


def record_recommendation_created(
    memory: CorporateMemoryDomainService | None,
    *,
    recommendation: Recommendation,
    actor_id: str = "system",
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=recommendation.tenant_id,
            brand_id=recommendation.brand_id,
            event_type="RecommendationCreated",
            actor=Actor(type="system" if actor_id == "system" else "user", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Recommendation", id=recommendation.recommendation_id),
                EntityRef(type="Brand", id=recommendation.brand_id),
            ),
            payload={
                "title": recommendation.title,
                "action": recommendation.action,
                "priority": recommendation.priority,
                "priority_score": recommendation.priority_score,
                "source": recommendation.source,
                "status": recommendation.status,
            },
            summary=f"Recomendación creada: {recommendation.title}",
        )
    )


def record_daily_roadmap_generated(
    memory: CorporateMemoryDomainService | None,
    *,
    roadmap: DailyRoadmap,
    recommendation_count: int,
    actor_id: str = "system",
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=roadmap.tenant_id,
            event_type="DailyRoadmapGenerated",
            actor=Actor(type="system" if actor_id == "system" else "user", id=actor_id),
            timestamp="",
            entity_refs=(EntityRef(type="DailyRoadmap", id=roadmap.roadmap_id),),
            payload={
                "roadmap_date": roadmap.roadmap_date,
                "generator_version": roadmap.generator_version,
                "recommendation_count": recommendation_count,
                "summary": roadmap.summary,
            },
            summary=f"Roadmap diario generado: {roadmap.roadmap_date} ({recommendation_count} recomendaciones)",
        )
    )


def record_recommendation_accepted(
    memory: CorporateMemoryDomainService | None,
    *,
    recommendation: Recommendation,
    actor_id: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=recommendation.tenant_id,
            brand_id=recommendation.brand_id,
            event_type="RecommendationAccepted",
            actor=Actor(type="user", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Recommendation", id=recommendation.recommendation_id),
                EntityRef(type="Brand", id=recommendation.brand_id),
            ),
            payload={
                "title": recommendation.title,
                "action": recommendation.action,
                "status": recommendation.status,
            },
            summary=f"Recomendación aprobada: {recommendation.title}",
        )
    )


def record_recommendation_rejected(
    memory: CorporateMemoryDomainService | None,
    *,
    recommendation: Recommendation,
    actor_id: str,
    reason: str,
) -> None:
    if memory is None:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=recommendation.tenant_id,
            brand_id=recommendation.brand_id,
            event_type="RecommendationRejected",
            actor=Actor(type="user", id=actor_id),
            timestamp="",
            entity_refs=(
                EntityRef(type="Recommendation", id=recommendation.recommendation_id),
                EntityRef(type="Brand", id=recommendation.brand_id),
            ),
            payload={
                "title": recommendation.title,
                "action": recommendation.action,
                "status": recommendation.status,
                "reason": reason,
            },
            summary=f"Recomendación rechazada: {recommendation.title}",
        )
    )
