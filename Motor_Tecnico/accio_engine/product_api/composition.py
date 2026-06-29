from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.product_application.use_cases import GetProduct, ListProducts
from Motor_Tecnico.accio_engine.product_domain.service import ProductDomainService
from Motor_Tecnico.accio_engine.product_infrastructure.application_adapters import ProductRbacAdapter
from Motor_Tecnico.accio_engine.product_infrastructure.composite_repository import CompositeProductRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema
from Motor_Tecnico.accio_engine.product_application.context import TenantAppContext


def build_product_domain_service() -> ProductDomainService:
    ensure_schema()
    return ProductDomainService(CompositeProductRepository())


class ProductUseCases:
    def __init__(self) -> None:
        products = build_product_domain_service()
        auth = ProductRbacAdapter()
        self.list_products = ListProducts(products, auth)
        self.get_product = GetProduct(products, auth)


_USE_CASES: ProductUseCases | None = None


def product_use_cases() -> ProductUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = ProductUseCases()
    return _USE_CASES


def reset_product_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_app_context(tenant_id: str, app_id: str) -> TenantAppContext:
    return TenantAppContext(
        tenant_id=tenant_id,
        app_id=marketing_app.normalize_app_id(app_id),
    )
