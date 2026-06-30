from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Motor_Tecnico.accio_engine.brand_domain.model import Brand
    from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain
    from Motor_Tecnico.accio_engine.lead_domain.model import Lead
    from Motor_Tecnico.accio_engine.publication_domain.model import Publication


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Read-only view of M1–M9 aggregates for Decision Engine rules."""

    tenant_id: str
    company_id: str
    generated_at: str
    brands: tuple["Brand", ...] = ()
    publications_by_brand: dict[str, tuple["Publication", ...]] = field(default_factory=dict)
    company_brain: "CompanyBrain | None" = None
    leads_by_brand: dict[str, tuple["Lead", ...]] = field(default_factory=dict)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def brain_profile(self) -> dict[str, Any]:
        if self.company_brain is None:
            return {}
        return dict(self.company_brain.profile or {})

    def brand_by_id(self, brand_id: str) -> "Brand | None":
        for brand in self.brands:
            key = brand.legacy_app_id or brand.brand_id
            if key == brand_id:
                return brand
        return None
