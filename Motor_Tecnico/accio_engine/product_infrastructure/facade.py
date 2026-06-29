"""Facade for settings_center and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import product_sql_enabled
from Motor_Tecnico.accio_engine.product_domain.service import ProductDomainService
from Motor_Tecnico.accio_engine.product_infrastructure.composite_repository import CompositeProductRepository

_SERVICE: ProductDomainService | None = None


def get_product_service() -> ProductDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = ProductDomainService(CompositeProductRepository())
    return _SERVICE


def reset_product_service() -> None:
    global _SERVICE
    _SERVICE = None


def product_store_active() -> bool:
    return product_sql_enabled()


def load_products(tenant_id: str) -> dict:
    return get_product_service().load_catalog(tenant_id)


def save_products(tenant_id: str, payload: dict) -> dict:
    return get_product_service().save_catalog(tenant_id, payload)
