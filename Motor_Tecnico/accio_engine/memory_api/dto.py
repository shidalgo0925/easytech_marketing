"""DTO — MemoryEvent API responses."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.memory_domain.model import MemoryEvent


def event_to_response(event: MemoryEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "tenant_id": event.tenant_id,
        "brand_id": event.brand_id,
        "event_type": event.event_type,
        "actor": {"type": event.actor.type, "id": event.actor.id},
        "timestamp": event.timestamp,
        "entity_refs": [{"type": r.type, "id": r.id} for r in event.entity_refs],
        "payload": event.payload,
        "summary": event.summary,
        "correlation_id": event.correlation_id,
    }
