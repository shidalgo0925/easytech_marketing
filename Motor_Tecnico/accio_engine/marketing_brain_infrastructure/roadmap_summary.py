"""Merge Marketing Brain output into DailyRoadmap.summary."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RoadmapEnrichmentResult


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_ai_roadmap_summary(result: RoadmapEnrichmentResult) -> dict[str, Any]:
    models = sorted(
        {
            item.enrichment.model
            for item in result.items
            if item.enrichment is not None and item.enrichment.model
        }
    )
    highlights = [
        {
            "recommendation_id": item.recommendation_id,
            "reason": (item.enrichment.reason if item.enrichment else "")[:200],
        }
        for item in result.items
        if item.enrichment is not None
    ][:8]
    return {
        "enriched_at": _utc_now(),
        "enriched_count": result.enriched_count,
        "skipped_count": result.skipped_count,
        "failed_count": result.failed_count,
        "models": models,
        "highlights": highlights,
    }
