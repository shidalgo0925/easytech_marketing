from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.opportunity_domain.errors import OpportunityNotFound
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.ports import OpportunityKnowledgeReader, OpportunityRepository
from Motor_Tecnico.accio_engine.opportunity_infrastructure.mapper import candidate_to_opportunity
from Motor_Tecnico.accio_engine.opportunity_infrastructure.matrix_enricher import enrich_opportunity_candidate
from Motor_Tecnico.accio_engine.opportunity_infrastructure.rules import evaluate_all_opportunity_rules


@dataclass(frozen=True)
class PersistedOpportunity:
    opportunity: Opportunity
    created: bool


@dataclass(frozen=True)
class DetectionResult:
    items: list[PersistedOpportunity]
    created_count: int
    updated_count: int

    @property
    def opportunities(self) -> list[Opportunity]:
        return [item.opportunity for item in self.items]


class OpportunityDetectionService:
    """F1 — rule-based opportunity detection (sin IA)."""

    def __init__(
        self,
        repository: OpportunityRepository,
        knowledge_reader: OpportunityKnowledgeReader,
    ) -> None:
        self._repo = repository
        self._reader = knowledge_reader

    def detect(
        self,
        tenant_id: str,
        *,
        reference_at: datetime | None = None,
    ) -> DetectionResult:
        ref = reference_at or datetime.now(timezone.utc)
        snapshot = self._reader.read(tenant_id)
        candidates = evaluate_all_opportunity_rules(snapshot, reference_at=ref)
        candidates = [enrich_opportunity_candidate(tenant_id, c) for c in candidates]

        persisted: list[PersistedOpportunity] = []
        created_count = 0
        updated_count = 0
        for candidate in candidates:
            row, created = self._repo.upsert(candidate_to_opportunity(tenant_id, candidate))
            persisted.append(PersistedOpportunity(opportunity=row, created=created))
            if created:
                created_count += 1
            else:
                updated_count += 1
        return DetectionResult(
            items=persisted,
            created_count=created_count,
            updated_count=updated_count,
        )

    def get_opportunity(self, tenant_id: str, opportunity_id: str) -> Opportunity:
        row = self._repo.get(tenant_id, opportunity_id)
        if row is None:
            raise OpportunityNotFound(opportunity_id)
        return row

    def list_opportunities(
        self,
        tenant_id: str,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Opportunity]:
        return self._repo.list_opportunities(
            tenant_id,
            brand_id=brand_id,
            status=status,
            limit=limit,
        )
