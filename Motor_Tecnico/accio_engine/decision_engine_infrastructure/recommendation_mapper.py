from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation, RecommendationCandidate


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_recommendation_id() -> str:
    return f"rec_{secrets.token_hex(6)}"


def candidate_to_recommendation(
    tenant_id: str,
    candidate: RecommendationCandidate,
    *,
    recommendation_id: str | None = None,
    created_by: str = "system",
    roadmap_id: str | None = None,
    now: str | None = None,
) -> Recommendation:
    ts = now or _utc_now()
    return Recommendation(
        tenant_id=tenant_id,
        recommendation_id=recommendation_id or new_recommendation_id(),
        company_id=tenant_id,
        brand_id=candidate.brand_id,
        roadmap_id=roadmap_id,
        title=candidate.title,
        description=candidate.description,
        action=candidate.action,
        reason=candidate.reason,
        priority=candidate.priority,
        priority_score=candidate.priority_score,
        owner_role=candidate.owner_role,
        status="pending_approval",
        source=candidate.source,
        confidence=candidate.confidence,
        justification_refs=dict(candidate.justification_refs),
        created_by=created_by,
        created_at=ts,
        updated_at=ts,
    )


def recommendation_to_row(rec: Recommendation) -> dict[str, Any]:
    return {
        "tenant_id": rec.tenant_id,
        "recommendation_id": rec.recommendation_id,
        "company_id": rec.company_id,
        "brand_id": rec.brand_id,
        "roadmap_id": rec.roadmap_id,
        "title": rec.title,
        "description": rec.description,
        "action": rec.action,
        "reason": rec.reason,
        "expected_roi": rec.expected_roi,
        "priority": rec.priority,
        "priority_score": rec.priority_score,
        "owner_role": rec.owner_role,
        "owner_id": rec.owner_id,
        "due_at": rec.due_at,
        "status": rec.status,
        "source": rec.source,
        "confidence": rec.confidence,
        "justification_refs_json": json.dumps(rec.justification_refs or {}, ensure_ascii=False),
        "dependencies_json": json.dumps(rec.dependencies or [], ensure_ascii=False),
        "created_by": rec.created_by,
        "approved_by": rec.approved_by,
        "rejected_by": rec.rejected_by,
        "executed_at": rec.executed_at,
        "result_json": json.dumps(rec.result) if rec.result is not None else None,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }


def row_to_recommendation(row: Any) -> Recommendation:
    return Recommendation(
        tenant_id=row["tenant_id"],
        recommendation_id=row["recommendation_id"],
        company_id=row["company_id"],
        brand_id=row["brand_id"],
        roadmap_id=row["roadmap_id"],
        title=row["title"],
        description=row["description"] or "",
        action=row["action"],
        reason=row["reason"],
        expected_roi=row["expected_roi"] or "",
        priority=row["priority"],
        priority_score=float(row["priority_score"] or 0.0),
        owner_role=row["owner_role"],
        owner_id=row["owner_id"],
        due_at=row["due_at"],
        status=row["status"],
        source=row["source"],
        confidence=float(row["confidence"] or 1.0),
        justification_refs=json.loads(row["justification_refs_json"] or "{}"),
        dependencies=json.loads(row["dependencies_json"] or "[]"),
        created_by=row["created_by"],
        approved_by=row["approved_by"],
        rejected_by=row["rejected_by"],
        executed_at=row["executed_at"],
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
