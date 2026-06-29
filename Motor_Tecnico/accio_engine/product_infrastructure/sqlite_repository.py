"""SQLite adapter — products table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.product_infrastructure.legacy_mapper import (
    catalog_to_products,
    product_to_row,
    products_to_catalog,
    row_to_product,
)


class SqliteProductRepository:
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._external = connection
        if connection is not None:
            ensure_schema(connection)

    def _conn(self) -> sqlite3.Connection:
        if self._external is not None:
            return self._external
        conn = get_connection()
        ensure_schema(conn)
        return conn

    def load_catalog(self, tenant_id: str) -> dict:
        products = self._list_all(tenant_id)
        return products_to_catalog(products)

    def save_catalog(self, tenant_id: str, data: dict) -> dict:
        products = catalog_to_products(tenant_id, data)
        self._save_all(tenant_id, products)
        return products_to_catalog(products)

    def list_products(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        active_only: bool = True,
    ) -> list[Product]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM products WHERE tenant_id = ? AND brand_id = ?"
            params: list[str] = [tenant_id, brand_id]
            if active_only:
                sql += " AND status = 'active'"
            sql += " ORDER BY name COLLATE NOCASE"
            rows = conn.execute(sql, params).fetchall()
            return [row_to_product(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_product(self, tenant_id: str, brand_id: str, product_id: str) -> Product | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT * FROM products
                WHERE tenant_id = ? AND brand_id = ?
                  AND (product_id = ? OR slug = ?)
                """,
                (tenant_id, brand_id, product_id, product_id),
            ).fetchone()
            return row_to_product(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def _list_all(self, tenant_id: str) -> list[Product]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM products WHERE tenant_id = ? ORDER BY brand_id, name COLLATE NOCASE",
                (tenant_id,),
            ).fetchall()
            return [row_to_product(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def _save_all(self, tenant_id: str, products: list[Product]) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM products WHERE tenant_id = ?", (tenant_id,))
            for product in products:
                conn.execute(
                    """
                    INSERT INTO products (
                      tenant_id, product_id, brand_id, slug, name, status,
                      landing_path, cta, payload_json, created_at, updated_at
                    ) VALUES (
                      :tenant_id, :product_id, :brand_id, :slug, :name, :status,
                      :landing_path, :cta, :payload_json, :created_at, :updated_at
                    )
                    """,
                    product_to_row(product),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_tenant(self, tenant_id: str, products: list[Product]) -> None:
        self._save_all(tenant_id, products)
