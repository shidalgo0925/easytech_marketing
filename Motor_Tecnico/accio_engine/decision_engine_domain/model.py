from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

RECOMMENDATION_STATUSES = frozenset(
    {
        "draft",
        "pending_approval",
        "approved",
        "in_progress",
        "done",
        "rejected",
        "snoozed",
    }
)

PRIORITIES = frozenset({"high", "medium", "low"})


@dataclass(frozen=True)
class RecommendationCandidate:
    """Pre-persistence output from Decision Engine rules (M10.1+)."""

    brand_id: str
    title: str
    description: str
    action: str
    reason: str
    priority: str
    owner_role: str
    source: str
    confidence: float = 1.0
    priority_score: float = 0.0
    justification_refs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "reason": self.reason,
            "priority": self.priority,
            "priority_score": self.priority_score,
            "owner_role": self.owner_role,
            "source": self.source,
            "confidence": self.confidence,
            "justification_refs": self.justification_refs,
            "status": "draft",
        }


def priority_from_score(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


@dataclass(frozen=True)
class Recommendation:
    """Persisted decision unit — M10.3."""

    tenant_id: str
    recommendation_id: str
    company_id: str
    brand_id: str
    title: str
    action: str
    reason: str
    priority: str
    owner_role: str
    source: str
    status: str
    created_by: str
    created_at: str
    updated_at: str
    description: str = ""
    expected_roi: str = ""
    priority_score: float = 0.0
    confidence: float = 1.0
    roadmap_id: str | None = None
    owner_id: str | None = None
    due_at: str | None = None
    justification_refs: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    approved_by: str | None = None
    rejected_by: str | None = None
    executed_at: str | None = None
    result: dict[str, Any] | None = None

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "tenant_id": self.tenant_id,
            "company_id": self.company_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "roadmap_id": self.roadmap_id,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "reason": self.reason,
            "expected_roi": self.expected_roi,
            "priority": self.priority,
            "priority_score": self.priority_score,
            "owner_role": self.owner_role,
            "owner_id": self.owner_id,
            "due_at": self.due_at,
            "status": self.status,
            "source": self.source,
            "confidence": self.confidence,
            "justification_refs": self.justification_refs,
            "dependencies": self.dependencies,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "rejected_by": self.rejected_by,
            "executed_at": self.executed_at,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


GENERATOR_VERSION = "decision_engine_v1"


@dataclass(frozen=True)
class DailyRoadmap:
    """Persisted daily container — M10.4."""

    tenant_id: str
    roadmap_id: str
    company_id: str
    roadmap_date: str
    generated_at: str
    generator_version: str = GENERATOR_VERSION
    summary: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self, *, recommendations: list[Recommendation] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "roadmap_id": self.roadmap_id,
            "tenant_id": self.tenant_id,
            "company_id": self.company_id,
            "roadmap_date": self.roadmap_date,
            "generated_at": self.generated_at,
            "generator_version": self.generator_version,
            "summary": self.summary,
        }
        if recommendations is not None:
            payload["recommendations"] = [r.to_api_dict() for r in recommendations]
        return payload
