from __future__ import annotations

from Motor_Tecnico.accio_engine.memory_application._authorization_helpers import require_read
from Motor_Tecnico.accio_engine.memory_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.memory_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.memory_application.query_inputs import GetMemoryEventQuery
from Motor_Tecnico.accio_engine.memory_domain.errors import MemoryDomainError
from Motor_Tecnico.accio_engine.memory_domain.model import MemoryEvent
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


class GetMemoryEvent:
    def __init__(
        self,
        memory: CorporateMemoryDomainService,
        authorization: AuthorizationPort,
    ) -> None:
        self._memory = memory
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, query: GetMemoryEventQuery) -> MemoryEvent:
        require_read(ctx, self._authorization)
        try:
            return self._memory.get(ctx.tenant_id, query.event_id)
        except MemoryDomainError as exc:
            raise ApplicationError.from_domain(exc) from exc
