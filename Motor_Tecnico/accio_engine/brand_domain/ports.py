from __future__ import annotations

from typing import Protocol

from .model import Brand


class BrandRepository(Protocol):
    def list_brands(self, tenant_id: str, *, active_only: bool = True) -> list[Brand]: ...

    def get_by_legacy_app_id(self, tenant_id: str, legacy_app_id: str) -> Brand | None: ...

    def get_by_brand_id(self, tenant_id: str, brand_id: str) -> Brand | None: ...

    def save_all(self, tenant_id: str, brands: list[Brand]) -> None: ...
