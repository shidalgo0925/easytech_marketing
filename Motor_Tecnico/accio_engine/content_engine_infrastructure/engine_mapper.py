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
    }


def row_to_piece(row: Any) -> ContentPiece:
    keys = row.keys() if hasattr(row, "keys") else []
    explain = json.loads(row["explain_json"]) if "explain_json" in keys and row["explain_json"] else None
    llm = json.loads(row["llm_enrichment_json"]) if "llm_enrichment_json" in keys and row["llm_enrichment_json"] else None
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
    )
