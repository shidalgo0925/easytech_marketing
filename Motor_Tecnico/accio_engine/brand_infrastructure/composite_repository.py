"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_domain.model import Brand
from Motor_Tecnico.accio_engine.brand_domain.ports import BrandRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import brand_json_enabled, brand_sql_enabled

from .json_repository import JsonBrandRepository
from .sqlite_repository import SqliteBrandRepository


class CompositeBrandRepository:
    def __init__(
        self,
        json_repo: BrandRepository | None = None,
        sql_repo: BrandRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonBrandRepository()
        self._sql = sql_repo or SqliteBrandRepository()

    def list_brands(self, tenant_id: str, *, active_only: bool = True) -> list[Brand]:
        if brand_sql_enabled():
            rows = self._sql.list_brands(tenant_id, active_only=active_only)
            if rows:
                return rows
        if brand_json_enabled():
            return self._json.list_brands(tenant_id, active_only=active_only)
        return []

    def get_by_legacy_app_id(self, tenant_id: str, legacy_app_id: str) -> Brand | None:
        if brand_sql_enabled():
            brand = self._sql.get_by_legacy_app_id(tenant_id, legacy_app_id)
            if brand is not None:
                return brand
        if brand_json_enabled():
            return self._json.get_by_legacy_app_id(tenant_id, legacy_app_id)
        return None

    def get_by_brand_id(self, tenant_id: str, brand_id: str) -> Brand | None:
        if brand_sql_enabled():
            brand = self._sql.get_by_brand_id(tenant_id, brand_id)
            if brand is not None:
                return brand
        if brand_json_enabled():
            return self._json.get_by_brand_id(tenant_id, brand_id)
        return None

    def save_all(self, tenant_id: str, brands: list[Brand]) -> None:
        if brand_sql_enabled():
            self._sql.save_all(tenant_id, brands)
