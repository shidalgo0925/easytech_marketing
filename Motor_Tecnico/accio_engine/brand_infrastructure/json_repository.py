"""JSON adapter — apps/registry.json."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.brand_domain.ports import BrandRepository

from .legacy_mapper import ensure_registry_bootstrapped, registry_to_brands


class JsonBrandRepository:
    def list_brands(self, tenant_id: str, *, active_only: bool = True) -> list[Brand]:
        ensure_registry_bootstrapped(tenant_id)
        brands = registry_to_brands(tenant_id)
        if active_only:
            brands = [b for b in brands if b.status == "active"]
        return sorted(brands, key=lambda b: (not b.is_default, b.name.lower()))

    def get_by_legacy_app_id(self, tenant_id: str, legacy_app_id: str) -> Brand | None:
        for brand in self.list_brands(tenant_id, active_only=False):
            if brand.legacy_app_id == legacy_app_id:
                return brand
        return None

    def get_by_brand_id(self, tenant_id: str, brand_id: str) -> Brand | None:
        return self.get_by_legacy_app_id(tenant_id, brand_id)

    def save_all(self, tenant_id: str, brands: list[Brand]) -> None:
        raise NotImplementedError("JsonBrandRepository is read-through legacy registry")
