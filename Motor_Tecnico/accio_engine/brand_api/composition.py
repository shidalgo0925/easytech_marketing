from __future__ import annotations

from Motor_Tecnico.accio_engine.brand_application.use_cases import GetBrand, ListBrands
from Motor_Tecnico.accio_engine.brand_domain.service import BrandDomainService
from Motor_Tecnico.accio_engine.brand_infrastructure.application_adapters import BrandRbacAdapter
from Motor_Tecnico.accio_engine.brand_infrastructure.composite_repository import CompositeBrandRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_brand_domain_service() -> BrandDomainService:
    ensure_schema()
    return BrandDomainService(CompositeBrandRepository())


class BrandUseCases:
    def __init__(self) -> None:
        brands = build_brand_domain_service()
        auth = BrandRbacAdapter()
        self.list_brands = ListBrands(brands, auth)
        self.get_brand = GetBrand(brands, auth)


_USE_CASES: BrandUseCases | None = None


def brand_use_cases() -> BrandUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = BrandUseCases()
    return _USE_CASES


def reset_brand_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None
