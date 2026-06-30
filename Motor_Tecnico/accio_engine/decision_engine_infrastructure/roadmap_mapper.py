from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap, GENERATOR_VERSION, Recommendation


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_roadmap_id(roadmap_date: str) -> str:
    return f"rdm_{roadmap_date.replace('-', '')}_{secrets.token_hex(4)}"


def build_roadmap_summary(recommendations: list[Recommendation]) -> dict[str, Any]:
    by_priority = {"high": 0, "medium": 0, "low": 0}
    by_brand: dict[str, int] = {}
    for rec in recommendations:
        by_priority[rec.priority] = by_priority.get(rec.priority, 0) + 1
        by_brand[rec.brand_id] = by_brand.get(rec.brand_id, 0) + 1
    return {
        "total": len(recommendations),
        "by_priority": by_priority,
        "by_brand": by_brand,
    }


def roadmap_to_row(roadmap: DailyRoadmap) -> dict[str, Any]:
    return {
        "tenant_id": roadmap.tenant_id,
        "roadmap_id": roadmap.roadmap_id,
        "company_id": roadmap.company_id,
        "roadmap_date": roadmap.roadmap_date,
        "generated_at": roadmap.generated_at,
        "generator_version": roadmap.generator_version,
        "summary_json": json.dumps(roadmap.summary or {}, ensure_ascii=False),
    }


def row_to_roadmap(row: Any) -> DailyRoadmap:
    return DailyRoadmap(
        tenant_id=row["tenant_id"],
        roadmap_id=row["roadmap_id"],
        company_id=row["company_id"],
        roadmap_date=row["roadmap_date"],
        generated_at=row["generated_at"],
        generator_version=row["generator_version"] or GENERATOR_VERSION,
        summary=json.loads(row["summary_json"] or "{}"),
    )


def reference_at_for_date(roadmap_date: str) -> datetime:
    """Noon America/Panama on roadmap_date — stable reference for rule evaluation."""
    from zoneinfo import ZoneInfo

    panama = ZoneInfo("America/Panama")
    year, month, day = (int(part) for part in roadmap_date.split("-"))
    return datetime(year, month, day, 12, 0, 0, tzinfo=panama)


def tenant_today_iso() -> str:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo("America/Panama")).strftime("%Y-%m-%d")
