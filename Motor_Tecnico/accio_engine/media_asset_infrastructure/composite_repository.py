"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import asset_json_enabled, asset_sql_enabled
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset
from Motor_Tecnico.accio_engine.media_asset_domain.ports import MediaAssetRepository

from .json_repository import JsonMediaAssetRepository
from .sqlite_repository import SqliteMediaAssetRepository


class CompositeMediaAssetRepository:
    def __init__(
        self,
        json_repo: MediaAssetRepository | None = None,
        sql_repo: MediaAssetRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonMediaAssetRepository()
        self._sql = sql_repo or SqliteMediaAssetRepository()

    def load_manifest(self, tenant_id: str) -> dict:
        if asset_sql_enabled():
            data = self._sql.load_manifest(tenant_id)
            if data.get("flyers") or data.get("extras"):
                return data
        if asset_json_enabled():
            return self._json.load_manifest(tenant_id)
        return {"flyers": [], "extras": []}

    def list_assets(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        if asset_sql_enabled():
            rows = self._sql.list_assets(tenant_id, brand_id=brand_id, asset_type=asset_type)
            if rows:
                return rows
        if asset_json_enabled():
            return self._json.list_assets(tenant_id, brand_id=brand_id, asset_type=asset_type)
        return []

    def get_asset(self, tenant_id: str, asset_id: str) -> MediaAsset | None:
        if asset_sql_enabled():
            row = self._sql.get_asset(tenant_id, asset_id)
            if row is not None:
                return row
        if asset_json_enabled():
            return self._json.get_asset(tenant_id, asset_id)
        return None
