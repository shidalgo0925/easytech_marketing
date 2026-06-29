from __future__ import annotations

from dataclasses import replace
from typing import Any

from .errors import CompanyBrainError, CompanyBrainNotFound
from .model import LEGACY_ALLOWED_KEYS, CompanyBrain
from .ports import Clock, CompanyBrainRepository


class CompanyBrainDomainService:
    def __init__(self, repository: CompanyBrainRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def get(self, tenant_id: str) -> CompanyBrain:
        brain = self._repository.get(tenant_id)
        if brain is None:
            raise CompanyBrainNotFound(tenant_id)
        return brain

    def get_or_empty(self, tenant_id: str) -> CompanyBrain:
        brain = self._repository.get(tenant_id)
        if brain is not None:
            return brain
        now = self._clock.now().isoformat()
        return CompanyBrain(
            tenant_id=tenant_id,
            company_id=tenant_id,
            profile={},
            status="draft",
            updated_at=now,
        )

    def patch(self, tenant_id: str, payload: dict[str, Any], *, actor_id: str) -> tuple[CompanyBrain, list[str]]:
        current = self.get_or_empty(tenant_id)
        profile = dict(current.profile)
        changed: list[str] = []
        for key in LEGACY_ALLOWED_KEYS:
            if key in payload:
                profile[key] = payload[key]
                changed.append(key)
        if not changed:
            raise CompanyBrainError("empty_patch", "No hay campos válidos para actualizar")
        now = self._clock.now().isoformat()
        profile["version"] = profile.get("version", 1)
        profile["updated_at"] = now[:10]
        updated = replace(
            current,
            profile=profile,
            status="published",
            updated_at=now,
            source="ui",
            last_synced_at=now,
            valid_from=current.valid_from or now,
        )
        self._repository.save(updated)
        return updated, changed
