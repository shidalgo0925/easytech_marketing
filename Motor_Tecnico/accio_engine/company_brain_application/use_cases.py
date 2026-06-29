from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.company_brain_application._authorization_helpers import (
    require_config_or_admin,
    require_read,
)
from Motor_Tecnico.accio_engine.company_brain_application.context import TenantContext
from Motor_Tecnico.accio_engine.company_brain_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.company_brain_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.company_brain_domain.errors import CompanyBrainError
from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
from Motor_Tecnico.accio_engine.company_brain_domain.service import CompanyBrainDomainService
from Motor_Tecnico.accio_engine.company_brain_infrastructure.memory_bridge import record_brain_updated
from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled


class GetCompanyBrain:
    def __init__(self, brain: CompanyBrainDomainService, authorization: AuthorizationPort) -> None:
        self._brain = brain
        self._authorization = authorization

    def __call__(self, ctx: TenantContext) -> CompanyBrain:
        require_read(ctx, self._authorization)
        try:
            return self._brain.get_or_empty(ctx.tenant_id)
        except CompanyBrainError as exc:
            raise ApplicationError.from_domain(exc) from exc


class UpdateCompanyBrain:
    def __init__(self, brain: CompanyBrainDomainService, authorization: AuthorizationPort) -> None:
        self._brain = brain
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, payload: dict[str, Any]) -> CompanyBrain:
        require_config_or_admin(ctx, self._authorization)
        try:
            brain, changed = self._brain.patch(ctx.tenant_id, payload, actor_id=ctx.actor_id)
        except CompanyBrainError as exc:
            raise ApplicationError.from_domain(exc) from exc
        if memory_sql_enabled() and changed:
            record_brain_updated(
                get_memory_domain_service(),
                tenant_id=ctx.tenant_id,
                actor_id=ctx.actor_id,
                fields_changed=changed,
            )
        return brain
