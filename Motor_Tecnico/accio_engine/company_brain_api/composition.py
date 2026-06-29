"""Composition root — Company Brain M2."""

from __future__ import annotations

from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.company_brain_application.use_cases import GetCompanyBrain, UpdateCompanyBrain
from Motor_Tecnico.accio_engine.company_brain_domain.service import CompanyBrainDomainService
from Motor_Tecnico.accio_engine.company_brain_infrastructure.application_adapters import CompanyBrainRbacAdapter
from Motor_Tecnico.accio_engine.company_brain_infrastructure.composite_repository import (
    CompositeCompanyBrainRepository,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


def build_company_brain_service() -> CompanyBrainDomainService:
    ensure_schema()
    return CompanyBrainDomainService(CompositeCompanyBrainRepository(), SystemClock())


class CompanyBrainUseCases:
    def __init__(self) -> None:
        brain = build_company_brain_service()
        auth = CompanyBrainRbacAdapter()
        self.get = GetCompanyBrain(brain, auth)
        self.update = UpdateCompanyBrain(brain, auth)


_USE_CASES: CompanyBrainUseCases | None = None


def company_brain_use_cases() -> CompanyBrainUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = CompanyBrainUseCases()
    return _USE_CASES


def reset_company_brain_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None
