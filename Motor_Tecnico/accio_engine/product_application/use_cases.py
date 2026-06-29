from __future__ import annotations

from Motor_Tecnico.accio_engine.product_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.product_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.product_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.product_domain.errors import ProductError
from Motor_Tecnico.accio_engine.product_domain.model import Product
from Motor_Tecnico.accio_engine.product_domain.service import ProductDomainService


class ListProducts:
    def __init__(self, products: ProductDomainService, authorization: AuthorizationPort) -> None:
        self._products = products
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext, *, active_only: bool = True) -> list[Product]:
        self._authorization.require_permission(ctx, "read")
        return self._products.list_products(ctx.tenant_id, ctx.app_id, active_only=active_only)


class GetProduct:
    def __init__(self, products: ProductDomainService, authorization: AuthorizationPort) -> None:
        self._products = products
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext, product_id: str) -> Product:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._products.get_product(ctx.tenant_id, ctx.app_id, product_id)
        except ProductError as exc:
            raise ApplicationError.from_domain(exc) from exc
