from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantAppContext:
    tenant_id: str
    app_id: str
