from __future__ import annotations

from dataclasses import dataclass
from typing import Any

LEGACY_ALLOWED_KEYS = frozenset({
    "empresa",
    "industria",
    "pais",
    "publico_objetivo",
    "productos_servicios",
    "diferenciadores",
    "problemas_que_resuelve",
    "tono_comunicacion",
    "objetivos_comerciales",
    "cta_principal",
    "contacto",
})


@dataclass(frozen=True)
class CompanyBrain:
    tenant_id: str
    company_id: str
    profile: dict[str, Any]
    status: str  # draft | published
    updated_at: str
    valid_from: str | None = None
    source: str | None = None
    last_synced_at: str | None = None

    def to_legacy_dict(self) -> dict[str, Any]:
        return dict(self.profile)
