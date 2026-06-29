"""Record CompanyBrain updates in Corporate Memory."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.memory_domain.model import Actor, EntityRef, MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


def record_brain_updated(
    memory: CorporateMemoryDomainService,
    *,
    tenant_id: str,
    actor_id: str,
    fields_changed: list[str],
) -> None:
    if not memory:
        return
    memory.record(
        MemoryEvent(
            event_id="",
            tenant_id=tenant_id,
            event_type="CompanyBrainUpdated",
            actor=Actor(type="user", id=actor_id),
            timestamp="",
            entity_refs=(EntityRef(type="CompanyBrain", id=tenant_id),),
            payload={"fields_changed": fields_changed},
            summary=f"Company Brain actualizado ({len(fields_changed)} campos)",
        )
    )
