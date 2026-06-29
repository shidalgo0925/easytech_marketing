"""JSON adapter — flyers/manifest.json."""

from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset
from Motor_Tecnico.accio_engine.media_asset_infrastructure.legacy_mapper import manifest_to_assets
from Motor_Tecnico.accio_engine.tenant import effective_paths, resolve_tenant


class JsonMediaAssetRepository:
    def _manifest_path(self, tenant_id: str) -> Path:
        return effective_paths(resolve_tenant(tenant_id))["flyers_manifest"]

    def _read_raw(self, tenant_id: str) -> dict:
        path = self._manifest_path(tenant_id)
        if not path.is_file():
            return {"flyers": [], "extras": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_manifest(self, tenant_id: str) -> dict:
        return self._read_raw(tenant_id)

    def list_assets(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        assets = manifest_to_assets(tenant_id, self._read_raw(tenant_id))
        if brand_id:
            assets = [a for a in assets if a.brand_id == brand_id]
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        return assets

    def get_asset(self, tenant_id: str, asset_id: str) -> MediaAsset | None:
        for asset in self.list_assets(tenant_id):
            if asset.asset_id == asset_id:
                return asset
        return None
