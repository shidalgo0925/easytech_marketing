"""JSON adapter — products.json per tenant."""

from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.product_infrastructure.legacy_mapper import (
    catalog_to_products,
    products_to_catalog,
)
from Motor_Tecnico.accio_engine.tenant import resolve_tenant


class JsonProductRepository:
    def _path(self, tenant_id: str) -> Path:
        return resolve_tenant(tenant_id).root / "products.json"

    def _read_raw(self, tenant_id: str) -> dict:
        path = self._path(tenant_id)
        if not path.is_file():
            return {"version": 1, "products": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_catalog(self, tenant_id: str) -> dict:
        return self._read_raw(tenant_id)

    def save_catalog(self, tenant_id: str, data: dict) -> dict:
        path = self._path(tenant_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return data

    def list_products(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        products = catalog_to_products(tenant_id, self._read_raw(tenant_id))
        rows = [p for p in products if p.brand_id == brand_id]
        if active_only:
            rows = [p for p in rows if p.status == "active"]
        return sorted(rows, key=lambda p: p.name.lower())

    def get_product(self, tenant_id: str, brand_id: str, product_id: str) -> Product | None:
        for product in self.list_products(tenant_id, brand_id, active_only=False):
            if product.product_id == product_id or product.slug == product_id:
                return product
        return None
