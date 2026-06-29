"""Bridge MarketingPlan domain events → Corporate Memory."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.marketing_plan_domain.events import (
    DomainEvent,
    PlanActivated,
    PlanCompleted,
    PlanCreated,
    PlanPaused,
)
from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


def marketing_plan_event_to_memory(event: DomainEvent) -> MemoryEvent:
    common = _common_fields(event)
    if isinstance(event, PlanCreated):
        return MemoryEvent(
            **common,
            event_type="PlanCreated",
            summary=f"Plan creado: {event.plan_id}",
            payload={"estado": str(event.estado), "created_by": event.created_by},
        )
    if isinstance(event, PlanActivated):
        return MemoryEvent(
            **common,
            event_type="PlanActivated",
            summary=f"Plan activado: {event.plan_id}",
            payload={
                "previous_active_plan_id": event.previous_active_plan_id,
                "resolution": event.resolution,
                "activated_by": event.activated_by,
            },
        )
    if isinstance(event, PlanPaused):
        return MemoryEvent(
            **common,
            event_type="PlanPaused",
            summary=f"Plan pausado: {event.plan_id}",
            payload={"paused_by": event.paused_by},
        )
    if isinstance(event, PlanCompleted):
        return MemoryEvent(
            **common,
            event_type="PlanCompleted",
            summary=f"Plan completado: {event.plan_id}",
            payload={"completed_by": event.completed_by},
        )
    raise TypeError(f"Unsupported domain event: {type(event)!r}")


def _common_fields(event: DomainEvent) -> dict[str, Any]:
    tenant_id = event.tenant_id
    app_id = event.app_id
    plan_id = event.plan_id
    occurred = event.occurred_at.isoformat()
    actor_id = _actor_from_event(event)
    return {
        "event_id": event.event_id,
        "tenant_id": tenant_id,
        "brand_id": app_id,
        "actor": Actor(type="user" if actor_id not in (None, "system") else "system", id=actor_id),
        "timestamp": occurred,
        "entity_refs": (EntityRef(type="MarketingPlan", id=plan_id),),
        "correlation_id": event.event_id,
    }


def _actor_from_event(event: DomainEvent) -> str | None:
    for field in ("created_by", "activated_by", "paused_by", "completed_by"):
        if hasattr(event, field):
            value = getattr(event, field)
            if value:
                return str(value)
    return None


def audit_entry_to_memory(tenant_id: str, entry: dict[str, Any]) -> MemoryEvent:
    """Map legacy assistant_audit.jsonl row → MemoryEvent."""
    event_id = str(entry.get("id") or entry.get("event_id") or "")
    app_id = entry.get("app_id")
    user = str(entry.get("user") or "system")
    return MemoryEvent(
        event_id=event_id or "",
        tenant_id=tenant_id,
        brand_id=str(app_id) if app_id else None,
        event_type="AssistantAudit",
        actor=Actor(type="user", id=user),
        timestamp=str(entry.get("at") or entry.get("timestamp") or ""),
        entity_refs=(EntityRef(type="AssistantSession", id=event_id or "unknown"),),
        payload={
            k: entry[k]
            for k in (
                "prompt",
                "response",
                "actions",
                "mode",
                "model",
                "cost_estimate",
                "context_view",
                "status",
            )
            if k in entry
        },
        summary=(str(entry.get("prompt") or "")[:120] or "Assistant interaction"),
        correlation_id=event_id or None,
    )


class MarketingPlanMemoryEventPublisher:
    """Implements marketing_plan DomainEventPublisher → Corporate Memory."""

    def __init__(self, memory: CorporateMemoryDomainService) -> None:
        self._memory = memory

    def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            memory_event = marketing_plan_event_to_memory(event)
            self._memory.record(memory_event)
