"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import product_json_enabled, product_sql_enabled
from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.product_domain.ports import ProductRepository

from .json_repository import JsonProductRepository
from .sqlite_repository import SqliteProductRepository


class CompositeProductRepository:
    def __init__(
        self,
        json_repo: ProductRepository | None = None,
        sql_repo: ProductRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonProductRepository()
        self._sql = sql_repo or SqliteProductRepository()

    def load_catalog(self, tenant_id: str) -> dict:
        if product_sql_enabled():
            data = self._sql.load_catalog(tenant_id)
            if data.get("products"):
                return data
        if product_json_enabled():
            return self._json.load_catalog(tenant_id)
        return {"version": 1, "products": []}

    def save_catalog(self, tenant_id: str, data: dict) -> dict:
        if product_sql_enabled():
            data = self._sql.save_catalog(tenant_id, data)
        if product_json_enabled():
            self._json.save_catalog(tenant_id, data)
        return data

    def list_products(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        if product_sql_enabled():
            rows = self._sql.list_products(tenant_id, brand_id, active_only=active_only)
            if rows:
                return rows
        if product_json_enabled():
            return self._json.list_products(tenant_id, brand_id, active_only=active_only)
        return []

    def get_product(self, tenant_id: str, brand_id: str, product_id: str) -> Product | None:
        if product_sql_enabled():
            row = self._sql.get_product(tenant_id, brand_id, product_id)
            if row is not None:
                return row
        if product_json_enabled():
            return self._json.get_product(tenant_id, brand_id, product_id)
        return None
