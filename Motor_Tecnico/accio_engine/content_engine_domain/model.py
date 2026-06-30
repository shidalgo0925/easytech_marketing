from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from Motor_Tecnico.accio_engine.content_engine_domain.constants import CONTENT_STATUSES


@dataclass(frozen=True)
class ContentPiece:
    tenant_id: str
    content_id: str
    brand_id: str
    title: str
    format: str = "post"
    channel: str = "linkedin"
    content_type: str = "valor"
    status: str = "draft"
    headline: str = ""
    body: str = ""
    call_to_action: str = ""
    hashtags: tuple[str, ...] = ()
    flyer_ref: str = ""
    objective: str = ""
    campaign_id: str | None = None
    recommendation_id: str | None = None
    explain: dict[str, Any] | None = None
    llm_enrichment: dict[str, Any] | None = None
    llm_skipped: bool = False
    planner_version: str = ""
    builder_version: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    approved_by: str = ""
    approved_at: str = ""
    rejected_reason: str = ""
    publish_channel: str = ""
    publish_status: str = ""
    published_at: str = ""
    publish_result: dict[str, Any] | None = None
    error_message: str = ""
    queue_post_id: str = ""

    @property
    def is_engine_content(self) -> bool:
        return bool(self.campaign_id) or self.status in CONTENT_STATUSES

    def to_api_dict(self) -> dict[str, Any]:
        result = self.publish_result or {}
        return {
            "content_id": self.content_id,
            "tenant_id": self.tenant_id,
            "brand_id": self.brand_id,
            "app_id": self.brand_id,
            "title": self.title,
            "format": self.format,
            "channel": self.channel,
            "content_type": self.content_type,
            "status": self.status,
            "headline": self.headline,
            "body": self.body,
            "call_to_action": self.call_to_action,
            "hashtags": list(self.hashtags),
            "flyer_ref": self.flyer_ref,
            "objective": self.objective,
            "campaign_id": self.campaign_id,
            "recommendation_id": self.recommendation_id,
            "explain": self.explain,
            "llm_enrichment": self.llm_enrichment,
            "llm_skipped": self.llm_skipped,
            "planner_version": self.planner_version,
            "builder_version": self.builder_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "approved_by": self.approved_by or None,
            "approved_at": self.approved_at or None,
            "rejected_reason": self.rejected_reason or None,
            "publish_channel": self.publish_channel or None,
            "publish_status": self.publish_status or None,
            "published_at": self.published_at or None,
            "publish_result": self.publish_result,
            "error_message": self.error_message or None,
            "queue_post_id": self.queue_post_id or None,
            "external_post_id": result.get("external_post_id"),
            "external_url": result.get("external_url"),
            "dry_run": result.get("dry_run", False),
            "is_engine_content": self.is_engine_content,
            **{k: v for k, v in (self.payload or {}).items() if k not in {
                "content_id", "tenant_id", "status",
            }},
        }
