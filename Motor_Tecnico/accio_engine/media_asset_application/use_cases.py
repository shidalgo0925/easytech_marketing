from __future__ import annotations

from Motor_Tecnico.accio_engine.media_asset_application.context import TenantContext
from Motor_Tecnico.accio_engine.media_asset_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.media_asset_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.media_asset_domain.errors import MediaAssetError
from Motor_Tecnico.accio_engine.media_asset_domain.model import MediaAsset
from Motor_Tecnico.accio_engine.media_asset_domain.service import MediaAssetDomainService


class ListMediaAssets:
    def __init__(self, assets: MediaAssetDomainService, authorization: AuthorizationPort) -> None:
        self._assets = assets
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        asset_type: str | None = None,
    ) -> list[MediaAsset]:
        self._authorization.require_permission(ctx, "read")
        return self._assets.list_assets(ctx.tenant_id, asset_type=asset_type)


class GetMediaAsset:
    def __init__(self, assets: MediaAssetDomainService, authorization: AuthorizationPort) -> None:
        self._assets = assets
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, asset_id: str) -> MediaAsset:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._assets.get_asset(ctx.tenant_id, asset_id)
        except MediaAssetError as exc:
            raise ApplicationError.from_domain(exc) from exc
