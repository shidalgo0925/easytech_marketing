"""Facade for dashboard_data and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import asset_sql_enabled
from Motor_Tecnico.accio_engine.media_asset_domain.service import MediaAssetDomainService
from Motor_Tecnico.accio_engine.media_asset_infrastructure.composite_repository import CompositeMediaAssetRepository

_SERVICE: MediaAssetDomainService | None = None


def get_media_asset_service() -> MediaAssetDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = MediaAssetDomainService(CompositeMediaAssetRepository())
    return _SERVICE


def reset_media_asset_service() -> None:
    global _SERVICE
    _SERVICE = None


def asset_store_active() -> bool:
    return asset_sql_enabled()


def load_flyers_manifest(tenant_id: str) -> dict:
    return get_media_asset_service().load_manifest(tenant_id)
