from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Product:
    tenant_id: str
    product_id: str
    brand_id: str
    slug: str
    name: str
    status: str = "active"
    landing_path: str = ""
    cta: str = "DIAGNÓSTICO"
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    @property
    def enabled(self) -> bool:
        return self.status == "active"

    def to_api_dict(self) -> dict[str, Any]:
        row = {
            "product_id": self.product_id,
            "tenant_id": self.tenant_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "slug": self.slug,
            "name": self.name,
            "status": self.status,
            "enabled": self.enabled,
            "landing_path": self.landing_path,
            "cta": self.cta,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        for key, value in (self.payload or {}).items():
            if key not in row and value is not None:
                row[key] = value
        return row

    def to_legacy_dict(self) -> dict[str, Any]:
        row = {
            "slug": self.slug,
            "name": self.name,
            "enabled": self.enabled,
            "landing_path": self.landing_path,
            "cta": self.cta,
        }
        hashtags = (self.payload or {}).get("hashtags")
        if hashtags:
            row["hashtags"] = hashtags
        return row
