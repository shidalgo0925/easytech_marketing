from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationContext:
    tenant_id: str
    app_id: str
    actor_id: str
    actor_role: str
