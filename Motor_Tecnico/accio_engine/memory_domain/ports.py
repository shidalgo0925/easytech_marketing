from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .model import MemoryEvent


class Clock(Protocol):
    def now(self) -> datetime: ...


class IdGenerator(Protocol):
    def new_memory_event_id(self) -> str: ...


class MemoryRepository(Protocol):
    def append(self, event: MemoryEvent) -> None: ...

    def get_by_id(self, tenant_id: str, event_id: str) -> MemoryEvent | None: ...

    def list_events(
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
    ) -> list[MemoryEvent]: ...
