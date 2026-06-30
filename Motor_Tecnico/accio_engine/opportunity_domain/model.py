from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OPPORTUNITY_STATUSES = frozenset({"detected", "classified", "approved", "dismissed"})
PRIORITIES = frozenset({"high", "medium", "low"})


@dataclass(frozen=True)
class OpportunityCandidate:
    """Pre-persistence signal from Opportunity Engine rules."""

    signal_key: str
    signal_type: str
    brand_id: str
    title: str
    description: str
    sector: str
    need: str
    product_slug: str
    channel: str
    landing_url: str
    priority: str
    source: str
    confidence: float = 1.0
    payload: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    reasoning: tuple[str, ...] = ()


@dataclass(frozen=True)
class Opportunity:
    tenant_id: str
    opportunity_id: str
    signal_key: str
    signal_type: str
    brand_id: str
    title: str
    description: str
    sector: str
    need: str
    product_slug: str
    channel: str
    landing_url: str
    priority: str
    status: str
    source: str
    confidence: float
    detected_at: str
    updated_at: str
    score: float = 0.0
    reasoning: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "tenant_id": self.tenant_id,
            "signal_key": self.signal_key,
            "signal_type": self.signal_type,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "title": self.title,
            "description": self.description,
            "sector": self.sector,
            "need": self.need,
            "product_slug": self.product_slug,
            "channel": self.channel,
            "landing_url": self.landing_url,
            "priority": self.priority,
            "status": self.status,
            "source": self.source,
            "confidence": self.confidence,
            "score": self.score,
            "reasoning": list(self.reasoning),
            "payload": self.payload,
            "detected_at": self.detected_at,
            "updated_at": self.updated_at,
        }
