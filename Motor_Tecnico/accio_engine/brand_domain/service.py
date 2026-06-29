from __future__ import annotations

from .errors import BrandError, BrandNotFound
from .model import Brand
from .ports import BrandRepository


class BrandDomainService:
    def __init__(self, repository: BrandRepository) -> None:
        self._repository = repository

    def list_brands(self, tenant_id: str, *, active_only: bool = True) -> list[Brand]:
        return self._repository.list_brands(tenant_id, active_only=active_only)

    def get_by_app_id(self, tenant_id: str, app_id: str) -> Brand:
        brand = self._repository.get_by_legacy_app_id(tenant_id, app_id)
        if brand is None:
            raise BrandNotFound(tenant_id, app_id)
        if brand.status != "active":
            raise BrandError("inactive", f"Brand inactive: {app_id}")
        return brand

    def get_by_brand_id(self, tenant_id: str, brand_id: str) -> Brand:
        brand = self._repository.get_by_brand_id(tenant_id, brand_id)
        if brand is None:
            raise BrandNotFound(tenant_id, brand_id)
        return brand
