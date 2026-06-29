from __future__ import annotations

from Motor_Tecnico.accio_engine.product_domain.errors import ProductNotFound
from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.product_domain.ports import ProductRepository


class ProductDomainService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repo = repository

    def load_catalog(self, tenant_id: str) -> dict:
        return self._repo.load_catalog(tenant_id)

    def save_catalog(self, tenant_id: str, data: dict) -> dict:
        return self._repo.save_catalog(tenant_id, data)

    def list_products(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        return self._repo.list_products(tenant_id, brand_id, active_only=active_only)

    def get_product(self, tenant_id: str, brand_id: str, product_id: str) -> Product:
        row = self._repo.get_product(tenant_id, brand_id, product_id)
        if row is None:
            raise ProductNotFound(f"Producto no encontrado: {product_id}")
        return row
