from __future__ import annotations

from datetime import datetime
from typing import Protocol

from .model import CompanyBrain


class Clock(Protocol):
    def now(self) -> datetime: ...


class CompanyBrainRepository(Protocol):
    def get(self, tenant_id: str) -> CompanyBrain | None: ...

    def save(self, brain: CompanyBrain) -> None: ...
