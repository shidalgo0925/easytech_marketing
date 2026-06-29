"""Facade for marketing_app and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_domain.errors import BrandError, BrandNotFound
from Motor_Tecnico.accio_engine.brand_domain.service import BrandDomainService
from Motor_Tecnico.accio_engine.brand_infrastructure.composite_repository import CompositeBrandRepository
from Motor_Tecnico.accio_engine.brand_infrastructure.legacy_mapper import brand_to_marketing_app
from Motor_Tecnico.accio_engine.marketing_app import AppNotFoundError, MarketingApp
from Motor_Tecnico.accio_engine.platform_infrastructure.db import brand_sql_enabled

_SERVICE: BrandDomainService | None = None


def get_brand_service() -> BrandDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = BrandDomainService(CompositeBrandRepository())
    return _SERVICE


def reset_brand_service() -> None:
    global _SERVICE
    _SERVICE = None


def list_marketing_apps(tenant_id: str, *, active_only: bool = True) -> list[MarketingApp]:
    brands = get_brand_service().list_brands(tenant_id, active_only=active_only)
    return [brand_to_marketing_app(b) for b in brands]


def get_marketing_app(tenant_id: str, app_id: str) -> MarketingApp:
    try:
        brand = get_brand_service().get_by_app_id(tenant_id, app_id)
    except BrandNotFound as exc:
        raise AppNotFoundError(exc.message) from exc
    except BrandError as exc:
        raise AppNotFoundError(exc.message) from exc
    return brand_to_marketing_app(brand)


def brand_store_active() -> bool:
    return brand_sql_enabled()
