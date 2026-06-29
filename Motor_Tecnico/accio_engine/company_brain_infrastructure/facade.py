"""Public facade for knowledge_api and legacy routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.company_brain_domain.service import CompanyBrainDomainService
from Motor_Tecnico.accio_engine.company_brain_infrastructure.composite_repository import (
    CompositeCompanyBrainRepository,
)


class _Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


_SERVICE: CompanyBrainDomainService | None = None


def get_company_brain_service() -> CompanyBrainDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = CompanyBrainDomainService(CompositeCompanyBrainRepository(), _Clock())
    return _SERVICE


def reset_company_brain_service() -> None:
    global _SERVICE
    _SERVICE = None


def load_business_context(tenant_id: str) -> dict[str, Any]:
    brain = get_company_brain_service().get_or_empty(tenant_id)
    return brain.to_legacy_dict()


def save_business_context(payload: dict[str, Any], tenant_id: str, *, actor_id: str = "system") -> dict[str, Any]:
    from Motor_Tecnico.accio_engine.company_brain_infrastructure.memory_bridge import record_brain_updated
    from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service
    from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled

    brain, changed = get_company_brain_service().patch(tenant_id, payload, actor_id=actor_id)
    if memory_sql_enabled() and changed:
        record_brain_updated(
            get_memory_domain_service(),
            tenant_id=tenant_id,
            actor_id=actor_id,
            fields_changed=changed,
        )
    return brain.to_legacy_dict()
