from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from .errors import MemoryEventNotFound, MemoryValidationError
from .model import MemoryEvent
from .ports import Clock, IdGenerator, MemoryRepository


class CorporateMemoryDomainService:
    def __init__(
        self,
        repository: MemoryRepository,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator

    def record(self, event: MemoryEvent) -> MemoryEvent:
        self._validate(event)
        stored = event
        if not event.event_id:
            stored = replace(event, event_id=self._id_generator.new_memory_event_id())
        if not event.timestamp:
            stored = replace(stored, timestamp=self._clock.now().isoformat())
        self._repository.append(stored)
        return stored

    def get(self, tenant_id: str, event_id: str) -> MemoryEvent:
        row = self._repository.get_by_id(tenant_id, event_id)
        if row is None:
            raise MemoryEventNotFound(event_id)
        return row

    def query(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        event_type: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        since: str | None = None,
        until: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MemoryEvent]:
        if limit < 1 or limit > 200:
            raise MemoryValidationError("invalid_limit", "limit must be 1..200")
        return self._repository.list_events(
            tenant_id,
            brand_id=brand_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )

    def _validate(self, event: MemoryEvent) -> None:
        if not event.tenant_id:
            raise MemoryValidationError("missing_tenant", "tenant_id is required")
        if not event.event_type:
            raise MemoryValidationError("missing_type", "event_type is required")
        if not event.entity_refs:
            raise MemoryValidationError("missing_refs", "entity_refs must not be empty")
        if event.actor.type not in {"user", "system"}:
            raise MemoryValidationError("invalid_actor", "actor.type must be user or system")
