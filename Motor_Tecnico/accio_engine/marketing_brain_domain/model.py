from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RecommendationEnrichment:
    """IA output for M11 — enriches text fields, never replaces recommendation identity."""

    reason: str
    description: str
    confidence: float
    model: str
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "description": self.description,
            "confidence": self.confidence,
            "model": self.model,
            "narrative": self.narrative,
        }


@dataclass(frozen=True)
class EnrichmentItemResult:
    recommendation_id: str
    enrichment: RecommendationEnrichment | None = None
    recommendation: dict[str, Any] | None = None
    persisted: bool = False
    skipped: bool = False
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "recommendation_id": self.recommendation_id,
            "persisted": self.persisted,
            "skipped": self.skipped,
        }
        if self.enrichment is not None:
            payload["enrichment"] = self.enrichment.to_dict()
        if self.recommendation is not None:
            payload["recommendation"] = self.recommendation
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class RoadmapEnrichmentResult:
    roadmap_id: str
    roadmap_date: str
    items: list[EnrichmentItemResult]
    enriched_count: int
    skipped_count: int
    failed_count: int
    persisted: bool
    roadmap_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "roadmap_id": self.roadmap_id,
            "roadmap_date": self.roadmap_date,
            "enriched_count": self.enriched_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "persisted": self.persisted,
            "items": [item.to_dict() for item in self.items],
        }
        if self.roadmap_summary is not None:
            payload["roadmap_summary"] = self.roadmap_summary
        return payload
