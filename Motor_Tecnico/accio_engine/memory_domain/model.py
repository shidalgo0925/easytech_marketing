from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EntityRef:
    type: str
    id: str


@dataclass(frozen=True)
class Actor:
    type: str  # user | system
    id: str | None = None


@dataclass(frozen=True)
class MemoryEvent:
    event_id: str
    tenant_id: str
    event_type: str
    actor: Actor
    timestamp: str
    entity_refs: tuple[EntityRef, ...]
    brand_id: str | None = None
    payload: dict[str, Any] | None = None
    summary: str | None = None
    correlation_id: str | None = None
