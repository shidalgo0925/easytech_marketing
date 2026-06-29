"""Serialize MemoryEvent ↔ SQLite row."""

from __future__ import annotations

import json
from typing import Any

from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent


def entity_refs_to_json(refs: tuple[EntityRef, ...]) -> str:
    return json.dumps([{"type": r.type, "id": r.id} for r in refs], ensure_ascii=False)


def entity_refs_from_json(raw: str) -> tuple[EntityRef, ...]:
    data = json.loads(raw or "[]")
    return tuple(EntityRef(type=str(item["type"]), id=str(item["id"])) for item in data)


def payload_to_json(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(payload, ensure_ascii=False)


def payload_from_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    return json.loads(raw)


def event_to_row(event: MemoryEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "tenant_id": event.tenant_id,
        "brand_id": event.brand_id,
        "event_type": event.event_type,
        "actor_type": event.actor.type,
        "actor_id": event.actor.id,
        "timestamp": event.timestamp,
        "entity_refs_json": entity_refs_to_json(event.entity_refs),
        "payload_json": payload_to_json(event.payload),
        "summary": event.summary,
        "correlation_id": event.correlation_id,
    }


def row_to_event(row: Any) -> MemoryEvent:
    return MemoryEvent(
        event_id=row["event_id"],
        tenant_id=row["tenant_id"],
        brand_id=row["brand_id"],
        event_type=row["event_type"],
        actor=Actor(type=row["actor_type"], id=row["actor_id"]),
        timestamp=row["timestamp"],
        entity_refs=entity_refs_from_json(row["entity_refs_json"]),
        payload=payload_from_json(row["payload_json"]),
        summary=row["summary"],
        correlation_id=row["correlation_id"],
    )
