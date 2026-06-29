"""Composition root — Corporate Memory M1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.memory_application.use_cases.queries.get_memory_event import GetMemoryEvent
from Motor_Tecnico.accio_engine.memory_application.use_cases.queries.list_memory_events import ListMemoryEvents
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.memory_infrastructure.application_adapters import MemoryRbacAuthorizationAdapter
from Motor_Tecnico.accio_engine.memory_infrastructure.sqlite_repository import SqliteMemoryRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UuidMemoryIdGenerator:
    def new_memory_event_id(self) -> str:
        return f"mem_{uuid.uuid4().hex[:12]}"


_MEMORY_SERVICE: CorporateMemoryDomainService | None = None


def get_memory_domain_service() -> CorporateMemoryDomainService:
    global _MEMORY_SERVICE
    if _MEMORY_SERVICE is None:
        ensure_schema()
        _MEMORY_SERVICE = CorporateMemoryDomainService(
            repository=SqliteMemoryRepository(),
            clock=SystemClock(),
            id_generator=UuidMemoryIdGenerator(),
        )
    return _MEMORY_SERVICE


def reset_memory_domain_service() -> None:
    global _MEMORY_SERVICE
    _MEMORY_SERVICE = None


class MemoryUseCases:
    def __init__(self) -> None:
        memory = get_memory_domain_service()
        auth = MemoryRbacAuthorizationAdapter()
        self.list_events = ListMemoryEvents(memory, auth)
        self.get_event = GetMemoryEvent(memory, auth)


_USE_CASES: MemoryUseCases | None = None


def memory_use_cases() -> MemoryUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = MemoryUseCases()
    return _USE_CASES


def reset_memory_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None
    reset_memory_domain_service()
