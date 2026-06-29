from __future__ import annotations

from Motor_Tecnico.accio_engine.media_asset_application.context import TenantContext
from Motor_Tecnico.accio_engine.media_asset_application.use_cases import GetMediaAsset, ListMediaAssets
from Motor_Tecnico.accio_engine.media_asset_domain.service import MediaAssetDomainService
from Motor_Tecnico.accio_engine.media_asset_infrastructure.application_adapters import MediaAssetRbacAdapter
from Motor_Tecnico.accio_engine.media_asset_infrastructure.composite_repository import CompositeMediaAssetRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_media_asset_domain_service() -> MediaAssetDomainService:
    ensure_schema()
    return MediaAssetDomainService(CompositeMediaAssetRepository())


class MediaAssetUseCases:
    def __init__(self) -> None:
        assets = build_media_asset_domain_service()
        auth = MediaAssetRbacAdapter()
        self.list_assets = ListMediaAssets(assets, auth)
        self.get_asset = GetMediaAsset(assets, auth)


_USE_CASES: MediaAssetUseCases | None = None


def media_asset_use_cases() -> MediaAssetUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = MediaAssetUseCases()
    return _USE_CASES


def reset_media_asset_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
