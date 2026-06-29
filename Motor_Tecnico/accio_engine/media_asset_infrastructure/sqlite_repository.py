"""SQLite adapter — media_assets table."""

from __future__ import annotations

import sqlite3

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset
from Motor_Tecnico.accio_engine.media_asset_infrastructure.legacy_mapper import (
    asset_to_row,
    assets_to_manifest,
    row_to_asset,
)


class SqliteMediaAssetRepository:
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

    def load_manifest(self, tenant_id: str) -> dict:
        assets = self.list_assets(tenant_id)
        return assets_to_manifest(assets)

    def list_assets(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM media_assets WHERE tenant_id = ?"
            params: list[str | int] = [tenant_id]
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            if asset_type:
                sql += " AND asset_type = ?"
                params.append(asset_type)
            sql += " ORDER BY (flyer_num IS NULL), flyer_num, title COLLATE NOCASE"
            rows = conn.execute(sql, params).fetchall()
            return [row_to_asset(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_asset(self, tenant_id: str, asset_id: str) -> MediaAsset | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM media_assets WHERE tenant_id = ? AND asset_id = ?",
                (tenant_id, asset_id),
            ).fetchone()
            return row_to_asset(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_tenant(self, tenant_id: str, assets: list[MediaAsset]) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM media_assets WHERE tenant_id = ?", (tenant_id,))
            for asset in assets:
                conn.execute(
                    """
                    INSERT INTO media_assets (
                      tenant_id, asset_id, brand_id, asset_type, uri, title,
                      status, flyer_num, payload_json, created_at, updated_at
                    ) VALUES (
                      :tenant_id, :asset_id, :brand_id, :asset_type, :uri, :title,
                      :status, :flyer_num, :payload_json, :created_at, :updated_at
                    )
                    """,
                    asset_to_row(asset),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
