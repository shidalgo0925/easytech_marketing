from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset


class MediaAssetRepository(Protocol):
    def load_manifest(self, tenant_id: str) -> dict:
        ...

    def list_assets(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        ...

    def get_asset(self, tenant_id: str, asset_id: str) -> MediaAsset | None:
        ...
