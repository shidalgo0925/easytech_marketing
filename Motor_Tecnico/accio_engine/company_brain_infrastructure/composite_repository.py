"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
from Motor_Tecnico.accio_engine.company_brain_domain.ports import CompanyBrainRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import (
    brain_json_enabled,
    brain_sql_enabled,
    brain_store_mode,
)

from .json_repository import JsonCompanyBrainRepository
from .sqlite_repository import SqliteCompanyBrainRepository


class CompositeCompanyBrainRepository:
    def __init__(
        self,
        json_repo: CompanyBrainRepository | None = None,
        sql_repo: CompanyBrainRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonCompanyBrainRepository()
        self._sql = sql_repo or SqliteCompanyBrainRepository()
        self._mode = brain_store_mode()

    def get(self, tenant_id: str) -> CompanyBrain | None:
        if brain_sql_enabled():
            brain = self._sql.get(tenant_id)
            if brain is not None:
                return brain
        if brain_json_enabled():
            return self._json.get(tenant_id)
        return None

    def save(self, brain: CompanyBrain) -> None:
        if brain_sql_enabled():
            self._sql.save(brain)
        if brain_json_enabled():
            self._json.save(brain)
