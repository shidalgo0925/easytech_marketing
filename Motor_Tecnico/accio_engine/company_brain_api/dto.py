from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain


def brain_to_response(brain: CompanyBrain) -> dict[str, Any]:
    return {
        "tenant_id": brain.tenant_id,
        "company_id": brain.company_id,
        "status": brain.status,
        "valid_from": brain.valid_from,
        "source": brain.source,
        "last_synced_at": brain.last_synced_at,
        "updated_at": brain.updated_at,
        "profile": brain.to_legacy_dict(),
    }
