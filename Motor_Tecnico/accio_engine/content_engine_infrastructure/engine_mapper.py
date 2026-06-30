"""Content Engine mappers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def piece_to_row(piece: ContentPiece) -> dict[str, Any]:
    return {
        "tenant_id": piece.tenant_id,
        "content_id": piece.content_id,
        "campaign_id": piece.campaign_id,
        "recommendation_id": piece.recommendation_id,
        "brand_id": piece.brand_id,
        "title": piece.title,
        "format": piece.format,
        "channel": piece.channel,
        "content_type": piece.content_type,
        "status": piece.status,
        "headline": piece.headline,
        "body": piece.body,
        "call_to_action": piece.call_to_action,
        "hashtags_json": json.dumps(list(piece.hashtags), ensure_ascii=False),
        "flyer_ref": piece.flyer_ref,
        "objective": piece.objective,
        "explain_json": json.dumps(piece.explain or {}, ensure_ascii=False) if piece.explain else None,
        "llm_enrichment_json": json.dumps(piece.llm_enrichment or {}, ensure_ascii=False)
        if piece.llm_enrichment
        else None,
        "llm_skipped": 1 if piece.llm_skipped else 0,
        "planner_version": piece.planner_version,
        "builder_version": piece.builder_version,
        "payload_json": json.dumps(piece.payload or {}, ensure_ascii=False),
        "created_at": piece.created_at or _utc_now(),
        "updated_at": piece.updated_at or _utc_now(),
        "approved_by": piece.approved_by or None,
        "approved_at": piece.approved_at or None,
        "rejected_reason": piece.rejected_reason or None,
        "publish_channel": piece.publish_channel or None,
        "publish_status": piece.publish_status or None,
        "published_at": piece.published_at or None,
        "publish_result_json": json.dumps(piece.publish_result or {}, ensure_ascii=False)
        if piece.publish_result
        else None,
        "error_message": piece.error_message or None,
        "queue_post_id": piece.queue_post_id or None,
    }


def row_to_piece(row: Any) -> ContentPiece:
    keys = row.keys() if hasattr(row, "keys") else []
    explain = json.loads(row["explain_json"]) if "explain_json" in keys and row["explain_json"] else None
    llm = json.loads(row["llm_enrichment_json"]) if "llm_enrichment_json" in keys and row["llm_enrichment_json"] else None
    pub_result = (
        json.loads(row["publish_result_json"])
        if "publish_result_json" in keys and row["publish_result_json"]
        else None
    )
    hashtags = tuple(json.loads(row["hashtags_json"] or "[]"))
    return ContentPiece(
        tenant_id=row["tenant_id"],
        content_id=row["content_id"],
        brand_id=row["brand_id"],
        title=row["title"],
        format=row["format"] or "post",
        channel=row["channel"] or "linkedin",
        content_type=row["content_type"] or "valor",
        status=row["status"],
        headline=row["headline"] or "",
        body=row["body"] or "",
        call_to_action=row["call_to_action"] or "",
        hashtags=hashtags,
        flyer_ref=row["flyer_ref"] or "",
        objective=row["objective"] or "",
        campaign_id=row["campaign_id"] if "campaign_id" in keys else None,
        recommendation_id=row["recommendation_id"] if "recommendation_id" in keys else None,
        explain=explain,
        llm_enrichment=llm,
        llm_skipped=bool(row["llm_skipped"]) if "llm_skipped" in keys else False,
        planner_version=row["planner_version"] if "planner_version" in keys else "",
        builder_version=row["builder_version"] if "builder_version" in keys else "",
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        approved_by=row["approved_by"] if "approved_by" in keys and row["approved_by"] else "",
        approved_at=row["approved_at"] if "approved_at" in keys and row["approved_at"] else "",
        rejected_reason=row["rejected_reason"] if "rejected_reason" in keys and row["rejected_reason"] else "",
        publish_channel=row["publish_channel"] if "publish_channel" in keys and row["publish_channel"] else "",
        publish_status=row["publish_status"] if "publish_status" in keys and row["publish_status"] else "",
        published_at=row["published_at"] if "published_at" in keys and row["published_at"] else "",
        publish_result=pub_result,
        error_message=row["error_message"] if "error_message" in keys and row["error_message"] else "",
        queue_post_id=row["queue_post_id"] if "queue_post_id" in keys and row["queue_post_id"] else "",
    )
