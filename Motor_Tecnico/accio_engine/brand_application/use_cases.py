from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_application.context import TenantContext
from Motor_Tecnico.accio_engine.brand_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.brand_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.brand_domain.errors import BrandError
from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.brand_domain.service import BrandDomainService


class ListBrands:
    def __init__(self, brands: BrandDomainService, authorization: AuthorizationPort) -> None:
        self._brands = brands
        self._authorization = authorization

    def __call__(self, ctx: TenantContext) -> list[Brand]:
        self._authorization.require_permission(ctx, "read")
        return self._brands.list_brands(ctx.tenant_id)


class GetBrand:
    def __init__(self, brands: BrandDomainService, authorization: AuthorizationPort) -> None:
        self._brands = brands
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, brand_id: str) -> Brand:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._brands.get_by_brand_id(ctx.tenant_id, brand_id)
        except BrandError as exc:
            raise ApplicationError.from_domain(exc) from exc
