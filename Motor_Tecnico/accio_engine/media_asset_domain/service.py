from __future__ import annotations

from Motor_Tecnico.accio_engine.media_asset_domain.errors import MediaAssetNotFound
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset
from Motor_Tecnico.accio_engine.media_asset_domain.ports import MediaAssetRepository


class MediaAssetDomainService:
    def __init__(self, repository: MediaAssetRepository) -> None:
        self._repo = repository

    def load_manifest(self, tenant_id: str) -> dict:
        return self._repo.load_manifest(tenant_id)

    def list_assets(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        return self._repo.list_assets(tenant_id, brand_id=brand_id, asset_type=asset_type)

    def get_asset(self, tenant_id: str, asset_id: str) -> MediaAsset:
        row = self._repo.get_asset(tenant_id, asset_id)
        if row is None:
            raise MediaAssetNotFound(f"Asset no encontrado: {asset_id}")
        return row
