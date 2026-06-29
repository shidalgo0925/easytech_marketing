"""JSON filesystem adapter — business_context.json."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
from Motor_Tecnico.accio_engine.company_brain_domain.ports import CompanyBrainRepository

from .legacy_mapper import legacy_to_brain, read_legacy_json, write_legacy_json


class JsonCompanyBrainRepository:
    def get(self, tenant_id: str) -> CompanyBrain | None:
        profile = read_legacy_json(tenant_id)
        if not profile:
            return None
        return legacy_to_brain(tenant_id, profile)

    def save(self, brain: CompanyBrain) -> None:
        write_legacy_json(brain.tenant_id, brain.profile)
