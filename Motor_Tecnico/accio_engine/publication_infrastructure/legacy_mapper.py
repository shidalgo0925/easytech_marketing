"""Legacy content_queue.json ↔ Publication."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine.publication_domain.model import Publication

_PLATFORM_EXTERNAL = {
    "linkedin": "linkedin_post_id",
    "facebook": "facebook_post_id",
    "instagram": "instagram_post_id",
}

_CORE_POST_KEYS = frozenset(
    {
        "id",
        "platform",
        "text",
        "status",
        "scheduled_at",
        "published_at",
        "app_id",
        "flyer",
        "campaign_id",
        "title",
        "linkedin_post_id",
        "facebook_post_id",
        "instagram_post_id",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _external_post_id(post: dict[str, Any]) -> str:
    platform = (post.get("platform") or "linkedin").lower()
    field = _PLATFORM_EXTERNAL.get(platform)
    if field and post.get(field):
        return str(post[field])
    for key in _PLATFORM_EXTERNAL.values():
        if post.get(key):
            return str(post[key])
    return str(post.get("external_post_id") or "")


def post_to_publication(tenant_id: str, brand_id: str, post: dict[str, Any]) -> Publication:
    post_id = str(post.get("id") or "")
    payload = {k: v for k, v in post.items() if k not in _CORE_POST_KEYS and v is not None}
    now = _utc_now()
    return Publication(
        tenant_id=tenant_id,
        publication_id=post_id,
        brand_id=brand_id,
        channel=str(post.get("platform") or "linkedin"),
        body=str(post.get("text") or ""),
        status=str(post.get("status") or "scheduled"),
        title=str(post.get("title") or ""),
        scheduled_at=str(post.get("scheduled_at") or ""),
        published_at=str(post.get("published_at") or ""),
        external_post_id=_external_post_id(post),
        flyer_ref=str(post.get("flyer") or ""),
        campaign_id=str(post.get("campaign_id") or ""),
        legacy_queue_id=post_id,
        payload=payload,
        created_at=str(post.get("created_at") or post.get("scheduled_at") or now),
        updated_at=now,
    )


def publication_to_post(pub: Publication) -> dict[str, Any]:
    post: dict[str, Any] = {
        "id": pub.legacy_queue_id or pub.publication_id,
        "platform": pub.channel,
        "text": pub.body,
        "status": pub.status,
        "scheduled_at": pub.scheduled_at,
        "app_id": pub.brand_id,
    }
    if pub.title:
        post["title"] = pub.title
    if pub.published_at:
        post["published_at"] = pub.published_at
    if pub.flyer_ref:
        post["flyer"] = pub.flyer_ref
    if pub.campaign_id:
        post["campaign_id"] = pub.campaign_id
    if pub.external_post_id:
        field = _PLATFORM_EXTERNAL.get(pub.channel.lower(), "linkedin_post_id")
        post[field] = pub.external_post_id
    if pub.created_at:
        post["created_at"] = pub.created_at
    for key, value in (pub.payload or {}).items():
        if key not in post and value is not None:
            post[key] = value
    return post


def queue_to_publications(tenant_id: str, brand_id: str, data: dict[str, Any]) -> list[Publication]:
    return [post_to_publication(tenant_id, brand_id, p) for p in data.get("posts", [])]


def publications_to_queue(publications: list[Publication]) -> dict[str, Any]:
    return {"posts": [publication_to_post(p) for p in publications]}


def publication_to_row(pub: Publication) -> dict[str, Any]:
    return {
        "tenant_id": pub.tenant_id,
        "publication_id": pub.publication_id,
        "brand_id": pub.brand_id,
        "channel": pub.channel,
        "title": pub.title,
        "body": pub.body,
        "status": pub.status,
        "scheduled_at": pub.scheduled_at,
        "published_at": pub.published_at,
        "external_post_id": pub.external_post_id,
        "flyer_ref": pub.flyer_ref,
        "campaign_id": pub.campaign_id,
        "legacy_queue_id": pub.legacy_queue_id,
        "payload_json": json.dumps(pub.payload or {}, ensure_ascii=False),
        "created_at": pub.created_at,
        "updated_at": pub.updated_at,
    }


def row_to_publication(row: Any) -> Publication:
    return Publication(
        tenant_id=row["tenant_id"],
        publication_id=row["publication_id"],
        brand_id=row["brand_id"],
        channel=row["channel"],
        body=row["body"],
        status=row["status"],
        title=row["title"] or "",
        scheduled_at=row["scheduled_at"] or "",
        published_at=row["published_at"] or "",
        external_post_id=row["external_post_id"] or "",
        flyer_ref=row["flyer_ref"] or "",
        campaign_id=row["campaign_id"] or "",
        legacy_queue_id=row["legacy_queue_id"] or row["publication_id"],
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
