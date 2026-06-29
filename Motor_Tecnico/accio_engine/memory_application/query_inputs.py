from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListMemoryEventsQuery:
    brand_id: str | None = None
    event_type: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    since: str | None = None
    until: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetMemoryEventQuery:
    event_id: str
