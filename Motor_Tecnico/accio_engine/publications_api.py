#!/usr/bin/env python3
"""Historial y acciones sobre publicaciones EM+Acción."""

from __future__ import annotations

import copy
import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine import executor, marketing_app, metrics_store
from Motor_Tecnico.accio_engine.editorial import editorial_label, normalize_status
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant

PANAMA = ZoneInfo("America/Panama")

_PLATFORM_URL_FIELDS = {
    "linkedin": "linkedin_post_id",
    "facebook": "facebook_post_id",
    "instagram": "instagram_post_id",
}


def _utc_now() -> str:
    return datetime.now(PANAMA).isoformat()


def _load_publish_log(tenant_id: str) -> list[dict[str, Any]]:
    path = effective_paths(resolve_tenant(tenant_id))["publish_log"]
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _log_by_post_id(tenant_id: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in _load_publish_log(tenant_id):
        pid = entry.get("id")
        if pid:
            grouped.setdefault(pid, []).append(entry)
    return grouped


def _flyer_url(flyer: str) -> str | None:
    if not flyer:
        return None
    name = Path(flyer).name
    if name.lower().endswith(".png"):
        return f"/accio/assets/flyers/{name}"
    return None


def _public_url(post: dict[str, Any], platform: str) -> str | None:
    field = _PLATFORM_URL_FIELDS.get(platform)
    if not field:
        return None
    remote = post.get(field)
    if not remote:
        return None
    if platform == "linkedin" and str(remote).startswith("urn:"):
        share_id = str(remote).split(":")[-1]
        return f"https://www.linkedin.com/feed/update/urn:li:share:{share_id}"
    return str(remote)


def _campaign_for_post(post_id: str, tenant_id: str, app_id: str) -> str:
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    camp_path = paths.get("campaigns")
    if not camp_path or not camp_path.is_file():
        return ""
    try:
        data = json.loads(camp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    for camp in data.get("campaigns", []):
        if camp.get("post_id") == post_id:
            return camp.get("id") or camp.get("product") or ""
    return ""


def _enrich_post(
    post: dict[str, Any],
    tenant_id: str,
    app_id: str,
    app_name: str,
    logs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    platform = post.get("platform") or "linkedin"
    status = normalize_status(post.get("status"))
    post_logs = logs.get(post.get("id", ""), [])
    last_log = post_logs[-1] if post_logs else {}
    metrics = metrics_store.aggregate(tenant_id, app_id, group_by="post_id")
    metric_row = next((m for m in metrics if m["key"] == post.get("id")), None)

    return {
        "id": post.get("id"),
        "tenant_id": tenant_id,
        "app_id": app_id,
        "app_name": app_name,
        "campaign_id": post.get("campaign_id") or _campaign_for_post(post.get("id", ""), tenant_id, app_id),
        "platform": platform,
        "status": status,
        "status_label": editorial_label(status),
        "created_at": post.get("created_at") or post.get("scheduled_at"),
        "scheduled_at": post.get("scheduled_at"),
        "published_at": post.get("published_at"),
        "text": post.get("text", ""),
        "flyer": post.get("flyer", ""),
        "flyer_url": _flyer_url(post.get("flyer", "")),
        "author": post.get("author") or post.get("created_by") or "",
        "approver": post.get("approver") or "",
        "connector_result": last_log.get("linkedin_post_id") or last_log.get("remote_post_id") or post.get("linkedin_post_id"),
        "public_url": _public_url(post, platform),
        "metrics": {"events": metric_row["count"] if metric_row else 0},
        "errors": post.get("error") or post.get("publish_error") or "",
        "is_reference": bool(post.get("is_reference")),
        "content_type": post.get("content_type_v2") or post.get("content_type"),
        "utm": post.get("utm"),
        "publish_log": post_logs,
    }


def _iter_app_queues(tenant_id: str, app_id: str | None) -> list[tuple[str, str, list[dict[str, Any]]]]:
    apps = marketing_app.list_apps(tenant_id, active_only=False)
    if app_id:
        aid = marketing_app.normalize_app_id(app_id)
        app = next((a for a in apps if a.app_id == aid), None)
        if not app:
            return []
        queue = executor.load_content_queue_for_app(tenant_id, aid)
        return [(aid, app.name, queue.get("posts", []))]

    rows: list[tuple[str, str, list[dict[str, Any]]]] = []
    for app in apps:
        queue = executor.load_content_queue_for_app(tenant_id, app.app_id)
        rows.append((app.app_id, app.name, queue.get("posts", [])))
    return rows


def list_publications(
    tenant_id: str = DEFAULT_TENANT,
    *,
    app_id: str | None = None,
    status: str | None = None,
    platform: str | None = None,
    campaign_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    logs = _log_by_post_id(tenant_id)
    items: list[dict[str, Any]] = []
    for aid, aname, posts in _iter_app_queues(tenant_id, app_id):
        for post in posts:
            row = _enrich_post(post, tenant_id, aid, aname, logs)
            if status and row["status"] != normalize_status(status):
                continue
            if platform and (row["platform"] or "").lower() != platform.lower():
                continue
            if campaign_id and row.get("campaign_id") != campaign_id:
                continue
            items.append(row)

    items.sort(key=lambda x: x.get("published_at") or x.get("scheduled_at") or x.get("created_at") or "", reverse=True)
    total = len(items)
    page = items[offset : offset + limit]
    return {
        "tenant_id": tenant_id,
        "app_id": app_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "publications": page,
        "status_counts": _status_counts(items),
    }


def _status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in items:
        st = row.get("status") or "unknown"
        counts[st] = counts.get(st, 0) + 1
    return counts


def find_publication(tenant_id: str, post_id: str, app_id: str | None = None) -> dict[str, Any] | None:
    logs = _log_by_post_id(tenant_id)
    for aid, aname, posts in _iter_app_queues(tenant_id, app_id):
        for post in posts:
            if post.get("id") == post_id:
                return _enrich_post(post, tenant_id, aid, aname, logs)
    return None


def _locate_post_raw(
    tenant_id: str, post_id: str, app_id: str | None = None
) -> tuple[str, dict[str, Any], dict[str, Any]] | None:
    for aid, _name, posts in _iter_app_queues(tenant_id, app_id):
        queue = executor.load_content_queue(tenant_id, aid)
        for i, post in enumerate(queue.get("posts", [])):
            if post.get("id") == post_id:
                return aid, post, queue
    return None


def duplicate_publication(
    tenant_id: str,
    post_id: str,
    *,
    app_id: str | None = None,
    platform: str | None = None,
    author: str = "",
) -> dict[str, Any]:
    located = _locate_post_raw(tenant_id, post_id, app_id)
    if not located:
        raise ValueError(f"Publicación no encontrada: {post_id}")
    aid, post, _queue = located
    new_post = copy.deepcopy(post)
    suffix = uuid.uuid4().hex[:6]
    base_id = re.sub(r"_copy_[a-f0-9]+$", "", post_id)
    new_post["id"] = f"{base_id}_copy_{suffix}"
    new_post["status"] = "draft"
    new_post["published_at"] = None
    new_post.pop("linkedin_post_id", None)
    new_post.pop("facebook_post_id", None)
    new_post.pop("instagram_post_id", None)
    new_post.pop("publish_error", None)
    if platform:
        new_post["platform"] = platform.lower()
    new_post["created_at"] = _utc_now()
    new_post["author"] = author or post.get("author") or ""
    new_post["duplicated_from"] = post_id
    scheduled = datetime.now(PANAMA) + timedelta(days=1)
    new_post["scheduled_at"] = scheduled.replace(hour=13, minute=0, second=0, microsecond=0).isoformat()
    return executor.enqueue_post(new_post, tenant_id, app_id=aid)


def archive_publication(tenant_id: str, post_id: str, app_id: str | None = None) -> dict[str, Any]:
    return executor.update_post_status(post_id, "archived", tenant_id, app_id)


def mark_reference(tenant_id: str, post_id: str, *, value: bool = True, app_id: str | None = None) -> dict[str, Any]:
    located = _locate_post_raw(tenant_id, post_id, app_id)
    if not located:
        raise ValueError(f"Publicación no encontrada: {post_id}")
    aid, post, queue = located
    post["is_reference"] = value
    executor.save_content_queue(queue, tenant_id, aid)
    return post


def reschedule_publication(
    tenant_id: str,
    post_id: str,
    scheduled_at: str,
    app_id: str | None = None,
) -> dict[str, Any]:
    located = _locate_post_raw(tenant_id, post_id, app_id)
    if not located:
        raise ValueError(f"Publicación no encontrada: {post_id}")
    aid, post, queue = located
    post["scheduled_at"] = scheduled_at
    if normalize_status(post.get("status")) in ("draft", "approved"):
        post["status"] = "scheduled"
    executor.save_content_queue(queue, tenant_id, aid)
    return post
