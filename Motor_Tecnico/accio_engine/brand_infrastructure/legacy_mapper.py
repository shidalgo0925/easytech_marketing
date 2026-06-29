"""Legacy apps/registry.json ↔ Brand."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.marketing_app import MarketingApp, bootstrap_registry, registry_path


def _load_registry_raw(tenant_id: str) -> dict[str, Any]:
    path = registry_path(tenant_id)
    if not path.is_file():
        bootstrap_registry(tenant_id)
    return json.loads(path.read_text(encoding="utf-8"))


def registry_to_brands(tenant_id: str) -> list[Brand]:
    reg = _load_registry_raw(tenant_id)
    now = datetime.now(timezone.utc).isoformat()
    brands: list[Brand] = []
    for raw in reg.get("apps", []):
        app_id = raw["app_id"]
        brands.append(
            Brand(
                tenant_id=tenant_id,
                brand_id=app_id,
                company_id=tenant_id,
                slug=raw.get("slug", app_id),
                name=raw.get("name", app_id),
                legacy_app_id=app_id,
                status=raw.get("status", "active"),
                is_default=bool(raw.get("is_default")),
                description=raw.get("description", ""),
                tone=raw.get("tone", ""),
                target_audience=raw.get("target_audience", ""),
                logo_url=raw.get("logo_url", ""),
                brand_colors=dict(raw.get("brand_colors") or {}),
                created_at=now,
                updated_at=reg.get("updated_at") or now,
            )
        )
    return brands


def brand_to_marketing_app(brand: Brand) -> MarketingApp:
    return MarketingApp(
        app_id=brand.legacy_app_id,
        tenant_id=brand.tenant_id,
        name=brand.name,
        slug=brand.slug,
        status=brand.status,
        is_default=brand.is_default,
        description=brand.description,
        tone=brand.tone,
        target_audience=brand.target_audience,
        logo_url=brand.logo_url,
        brand_colors=brand.brand_colors,
    )


def brand_to_row(brand: Brand) -> dict[str, Any]:
    return {
        "tenant_id": brand.tenant_id,
        "brand_id": brand.brand_id,
        "company_id": brand.company_id,
        "slug": brand.slug,
        "name": brand.name,
        "description": brand.description,
        "tone": brand.tone,
        "target_audience": brand.target_audience,
        "logo_url": brand.logo_url,
        "brand_colors_json": json.dumps(brand.brand_colors or {}, ensure_ascii=False),
        "status": brand.status,
        "is_default": 1 if brand.is_default else 0,
        "legacy_app_id": brand.legacy_app_id,
        "created_at": brand.created_at,
        "updated_at": brand.updated_at,
    }


def row_to_brand(row: Any) -> Brand:
    return Brand(
        tenant_id=row["tenant_id"],
        brand_id=row["brand_id"],
        company_id=row["company_id"],
        slug=row["slug"],
        name=row["name"],
        legacy_app_id=row["legacy_app_id"],
        status=row["status"],
        is_default=bool(row["is_default"]),
        description=row["description"] or "",
        tone=row["tone"] or "",
        target_audience=row["target_audience"] or "",
        logo_url=row["logo_url"] or "",
        brand_colors=json.loads(row["brand_colors_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def ensure_registry_bootstrapped(tenant_id: str) -> None:
    path = registry_path(tenant_id)
    if not path.is_file():
        bootstrap_registry(tenant_id)
