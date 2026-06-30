from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Motor_Tecnico.accio_engine.brand_domain.model import Brand
    from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
    from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
    from Motor_Tecnico.accio_engine.lead_domain.model import Lead
    from Motor_Tecnico.accio_engine.publication_domain.model import Publication


@dataclass(frozen=True)
class OpportunitySnapshot:
    """Read-only M2–M9 view for Opportunity Engine rules."""

    tenant_id: str
    company_id: str
    generated_at: str
    brands: tuple["Brand", ...] = ()
    publications_by_brand: dict[str, tuple["Publication", ...]] = field(default_factory=dict)
    campaigns_by_brand: dict[str, tuple["Campaign", ...]] = field(default_factory=dict)
    leads_by_brand: dict[str, tuple["Lead", ...]] = field(default_factory=dict)
    company_brain: "CompanyBrain | None" = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
