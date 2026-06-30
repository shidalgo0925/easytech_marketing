from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot


class OpportunityKnowledgeReader(Protocol):
    def read(self, tenant_id: str) -> OpportunitySnapshot: ...


class OpportunityRepository(Protocol):
    def upsert(self, opportunity: Opportunity) -> tuple[Opportunity, bool]: ...

    def get(self, tenant_id: str, opportunity_id: str) -> Opportunity | None: ...

    def get_by_signal_key(self, tenant_id: str, signal_key: str) -> Opportunity | None: ...

    def list_opportunities(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Opportunity]: ...

    def update(self, opportunity: Opportunity) -> None: ...
