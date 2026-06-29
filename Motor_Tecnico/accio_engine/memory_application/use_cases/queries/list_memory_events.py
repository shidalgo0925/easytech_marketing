from __future__ import annotations

from Motor_Tecnico.accio_engine.memory_application._authorization_helpers import require_read
from Motor_Tecnico.accio_engine.memory_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.memory_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.memory_application.query_inputs import ListMemoryEventsQuery
from Motor_Tecnico.accio_engine.memory_domain.errors import MemoryDomainError
from Motor_Tecnico.accio_engine.memory_domain.model import MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


class ListMemoryEvents:
    def __init__(
        self,
        memory: CorporateMemoryDomainService,
        authorization: AuthorizationPort,
    ) -> None:
        self._memory = memory
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, query: ListMemoryEventsQuery) -> list[MemoryEvent]:
        require_read(ctx, self._authorization)
        try:
            return self._memory.query(
                ctx.tenant_id,
                brand_id=query.brand_id,
                event_type=query.event_type,
                entity_type=query.entity_type,
                entity_id=query.entity_id,
                since=query.since,
                until=query.until,
                limit=query.limit,
                offset=query.offset,
            )
        except MemoryDomainError as exc:
            raise ApplicationError.from_domain(exc) from exc
