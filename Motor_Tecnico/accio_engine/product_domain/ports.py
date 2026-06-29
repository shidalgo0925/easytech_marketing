from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.product_domain.model import Product


class ProductRepository(Protocol):
    def load_catalog(self, tenant_id: str) -> dict:
        ...

    def save_catalog(self, tenant_id: str, data: dict) -> dict:
        ...

    def list_products(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        ...

    def get_product(self, tenant_id: str, brand_id: str, product_id: str) -> Product | None:
        ...
