from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from Motor_Tecnico.accio_engine.opportunity_domain.model import OpportunityCandidate
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot

from .brand_inactive import evaluate_brand_inactive
from .campaign_stalled import evaluate_campaign_stalled
from .lead_followup_gap import evaluate_lead_followup_gap

RuleEvaluator = Callable[..., list[OpportunityCandidate]]

ENABLED_RULES: tuple[RuleEvaluator, ...] = (
    evaluate_brand_inactive,
    evaluate_campaign_stalled,
    evaluate_lead_followup_gap,
)


def evaluate_all_opportunity_rules(
    snapshot: OpportunitySnapshot,
    *,
    reference_at: datetime | None = None,
) -> list[OpportunityCandidate]:
    ref = reference_at or datetime.now(timezone.utc)
    rows: list[OpportunityCandidate] = []
    for rule in ENABLED_RULES:
        rows.extend(rule(snapshot, reference_at=ref))
    return rows
