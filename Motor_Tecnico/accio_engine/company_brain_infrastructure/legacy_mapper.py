"""Legacy business_context.json ↔ CompanyBrain."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
from Motor_Tecnico.accio_engine.tenant import effective_paths, resolve_tenant


def legacy_path(tenant_id: str) -> Path:
    return effective_paths(resolve_tenant(tenant_id))["business_context"]


def read_legacy_json(tenant_id: str) -> dict[str, Any]:
    path = legacy_path(tenant_id)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_legacy_json(tenant_id: str, profile: dict[str, Any]) -> None:
    path = legacy_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def legacy_to_brain(tenant_id: str, profile: dict[str, Any]) -> CompanyBrain:
    now = datetime.now(timezone.utc).isoformat()
    updated = str(profile.get("updated_at") or now[:10])
    return CompanyBrain(
        tenant_id=tenant_id,
        company_id=tenant_id,
        profile=dict(profile),
        status="published" if profile else "draft",
        updated_at=updated,
        source="legacy_json",
        last_synced_at=now,
        valid_from=profile.get("valid_from"),
    )


def brain_to_row(brain: CompanyBrain) -> dict[str, Any]:
    return {
        "tenant_id": brain.tenant_id,
        "company_id": brain.company_id,
        "profile_json": json.dumps(brain.profile, ensure_ascii=False),
        "status": brain.status,
        "valid_from": brain.valid_from,
        "source": brain.source,
        "last_synced_at": brain.last_synced_at,
        "updated_at": brain.updated_at,
    }


def row_to_brain(row: Any) -> CompanyBrain:
    return CompanyBrain(
        tenant_id=row["tenant_id"],
        company_id=row["company_id"],
        profile=json.loads(row["profile_json"] or "{}"),
        status=row["status"],
        valid_from=row["valid_from"],
        source=row["source"],
        last_synced_at=row["last_synced_at"],
        updated_at=row["updated_at"],
    )
