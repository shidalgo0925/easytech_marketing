from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Brand:
    tenant_id: str
    brand_id: str
    company_id: str
    slug: str
    name: str
    legacy_app_id: str
    status: str = "active"
    is_default: bool = False
    description: str = ""
    tone: str = ""
    target_audience: str = ""
    logo_url: str = ""
    brand_colors: dict[str, str] | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "tenant_id": self.tenant_id,
            "company_id": self.company_id,
            "slug": self.slug,
            "name": self.name,
            "legacy_app_id": self.legacy_app_id,
            "app_id": self.legacy_app_id,
            "status": self.status,
            "is_default": self.is_default,
            "description": self.description,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "logo_url": self.logo_url,
            "brand_colors": self.brand_colors or {},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
