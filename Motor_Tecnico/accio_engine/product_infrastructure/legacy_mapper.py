"""Legacy products.json ↔ Product."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT

_LEGACY_KEYS = frozenset({"slug", "name", "enabled", "landing_path", "cta"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug_to_brand_id(tenant_id: str, slug: str) -> str:
    if tenant_id == DEFAULT_TENANT:
        mapped = marketing_app._PRODUCT_SLUG_TO_APP.get(slug)
        if mapped:
            return mapped
    return marketing_app.DEFAULT_APP_ID


def legacy_row_to_product(tenant_id: str, row: dict[str, Any]) -> Product:
    slug = (row.get("slug") or "").strip().lower()
    brand_id = row.get("brand_id") or slug_to_brand_id(tenant_id, slug)
    enabled = bool(row.get("enabled", True))
    payload = {k: v for k, v in row.items() if k not in _LEGACY_KEYS and k != "brand_id" and v is not None}
    now = _utc_now()
    return Product(
        tenant_id=tenant_id,
        product_id=slug,
        brand_id=brand_id,
        slug=slug,
        name=(row.get("name") or slug).strip(),
        status="active" if enabled else "disabled",
        landing_path=(row.get("landing_path") or "").strip(),
        cta=(row.get("cta") or "DIAGNÓSTICO").strip(),
        payload=payload,
        created_at=now,
        updated_at=now,
    )


def catalog_to_products(tenant_id: str, data: dict[str, Any]) -> list[Product]:
    return [legacy_row_to_product(tenant_id, row) for row in data.get("products", [])]


def products_to_catalog(products: list[Product], *, updated_at: str | None = None) -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": updated_at or _utc_now(),
        "products": [p.to_legacy_dict() for p in products],
    }


def product_to_row(product: Product) -> dict[str, Any]:
    return {
        "tenant_id": product.tenant_id,
        "product_id": product.product_id,
        "brand_id": product.brand_id,
        "slug": product.slug,
        "name": product.name,
        "status": product.status,
        "landing_path": product.landing_path,
        "cta": product.cta,
        "payload_json": json.dumps(product.payload or {}, ensure_ascii=False),
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }


def row_to_product(row: Any) -> Product:
    return Product(
        tenant_id=row["tenant_id"],
        product_id=row["product_id"],
        brand_id=row["brand_id"],
        slug=row["slug"],
        name=row["name"],
        status=row["status"],
        landing_path=row["landing_path"] or "",
        cta=row["cta"] or "DIAGNÓSTICO",
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
