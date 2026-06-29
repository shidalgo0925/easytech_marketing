"""SQLite adapter — brands table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.brand_domain.ports import BrandRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection

from .legacy_mapper import brand_to_row, row_to_brand


class SqliteBrandRepository:
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

    def list_brands(self, tenant_id: str, *, active_only: bool = True) -> list[Brand]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM brands WHERE tenant_id = ?"
            params: list[str] = [tenant_id]
            if active_only:
                sql += " AND status = 'active'"
            sql += " ORDER BY is_default DESC, name COLLATE NOCASE"
            rows = conn.execute(sql, params).fetchall()
            return [row_to_brand(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_by_legacy_app_id(self, tenant_id: str, legacy_app_id: str) -> Brand | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM brands WHERE tenant_id = ? AND legacy_app_id = ?",
                (tenant_id, legacy_app_id),
            ).fetchone()
            return row_to_brand(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def get_by_brand_id(self, tenant_id: str, brand_id: str) -> Brand | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM brands WHERE tenant_id = ? AND brand_id = ?",
                (tenant_id, brand_id),
            ).fetchone()
            return row_to_brand(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def save_all(self, tenant_id: str, brands: list[Brand]) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM brands WHERE tenant_id = ?", (tenant_id,))
            for brand in brands:
                conn.execute(
                    """
                    INSERT INTO brands (
                      tenant_id, brand_id, company_id, slug, name, description,
                      tone, target_audience, logo_url, brand_colors_json,
                      status, is_default, legacy_app_id, created_at, updated_at
                    ) VALUES (
                      :tenant_id, :brand_id, :company_id, :slug, :name, :description,
                      :tone, :target_audience, :logo_url, :brand_colors_json,
                      :status, :is_default, :legacy_app_id, :created_at, :updated_at
                    )
                    """,
                    brand_to_row(brand),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
