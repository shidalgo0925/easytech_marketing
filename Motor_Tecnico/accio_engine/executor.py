#!/usr/bin/env python3
"""Ejecuta acciones del motor Accio sobre componentes existentes (multi-tenant)."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python3"
PANAMA = ZoneInfo("America/Panama")


def _paths(tenant_id: str) -> dict[str, Path]:
    return effective_paths(resolve_tenant(tenant_id))


def _run_script(script: str, *args: str) -> dict[str, Any]:
    cmd = [str(VENV_PYTHON), str(BASE_DIR / "Motor_Tecnico" / script), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR), timeout=600)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:] if proc.stdout else "",
        "stderr": proc.stderr[-4000:] if proc.stderr else "",
    }


def run_pipeline(tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    scrape = _run_script("scraper_panama.py")
    if not scrape["ok"]:
        return {"tenant_id": tenant_id, "step": "scraper", **scrape}
    sync = _run_script("odoo_sync.py")
    return {"tenant_id": tenant_id, "step": "odoo_sync", "scrape": scrape, **sync}


def _tenant_args(tenant_id: str, app_id: str | None = None) -> list[str]:
    args = [f"--tenant-id={tenant_id}"]
    if app_id:
        args.append(f"--app-id={app_id}")
    return args


def publish_channel(
    connector_id: str,
    force: bool = False,
    dry_run: bool = False,
    tenant_id: str = DEFAULT_TENANT,
    app_id: str | None = None,
) -> dict[str, Any]:
    args = [f"--connector={connector_id}", *_tenant_args(tenant_id, app_id)]
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    result = _run_script("channel_publisher.py", *args)
    result["tenant_id"] = tenant_id
    return result


def publish_linkedin(
    force: bool = False,
    dry_run: bool = False,
    tenant_id: str = DEFAULT_TENANT,
    app_id: str | None = None,
) -> dict[str, Any]:
    args = [*_tenant_args(tenant_id, app_id)]
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    result = _run_script("linkedin_publisher.py", *args)
    result["tenant_id"] = tenant_id
    return result


def publish_meta(
    platform: str = "all",
    force: bool = False,
    dry_run: bool = False,
    tenant_id: str = DEFAULT_TENANT,
    app_id: str | None = None,
) -> dict[str, Any]:
    args = [f"--platform={platform}", *_tenant_args(tenant_id, app_id)]
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    result = _run_script("meta_publisher.py", *args)
    result["tenant_id"] = tenant_id
    return result


def _resolve_app_id(tenant_id: str, app_id: str | None) -> str:
    from Motor_Tecnico.accio_engine import marketing_app

    return marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))


def load_content_queue(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import marketing_app

    path = marketing_app.queue_file_path(tenant_id, app_id)
    if not path.is_file():
        return {"posts": []}
    return json.loads(path.read_text(encoding="utf-8"))


def load_content_queue_for_app(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import marketing_app

    aid = _resolve_app_id(tenant_id, app_id)
    data = load_content_queue(tenant_id, aid)
    posts = marketing_app.posts_for_app(data.get("posts", []), aid, tenant_id)
    return {**data, "posts": posts, "app_id": aid}


def save_content_queue(
    data: dict[str, Any], tenant_id: str = DEFAULT_TENANT, app_id: str | None = None
) -> None:
    from Motor_Tecnico.accio_engine import marketing_app

    path = marketing_app.queue_file_path(tenant_id, app_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def enqueue_post(
    post: dict[str, Any], tenant_id: str = DEFAULT_TENANT, app_id: str | None = None
) -> dict[str, Any]:
    required = {"id", "platform", "text", "scheduled_at"}
    missing = required - set(post.keys())
    if missing:
        raise ValueError(f"Faltan campos en post: {', '.join(sorted(missing))}")

    entry = {
        "id": post["id"],
        "platform": post["platform"],
        "status": post.get("status", "pending"),
        "scheduled_at": post["scheduled_at"],
        "flyer": post.get("flyer", ""),
        "utm": post.get("utm", ""),
        "text": post["text"],
        "first_comment": post.get("first_comment", ""),
    }
    for key in ("content_type", "content_type_v2", "topic_framework", "flyer_num"):
        if post.get(key) is not None:
            entry[key] = post[key]

    aid = _resolve_app_id(tenant_id, post.get("app_id") or app_id)
    entry["app_id"] = aid

    queue = load_content_queue(tenant_id, aid)
    posts = queue.setdefault("posts", [])
    for existing in posts:
        if existing.get("id") == entry["id"]:
            raise ValueError(f"Post id duplicado: {entry['id']}")
    posts.append(entry)
    save_content_queue(queue, tenant_id, aid)
    return entry


def enqueue_posts(posts: list[dict[str, Any]], tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    created = []
    errors = []
    for post in posts:
        try:
            created.append(enqueue_post(post, tenant_id))
        except ValueError as exc:
            errors.append({"id": post.get("id"), "error": str(exc)})
    return {"created": created, "errors": errors, "count": len(created)}


def set_calendar(calendar: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    path = _paths(tenant_id)["calendar"]
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(PANAMA).isoformat(),
        **calendar,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def _platform_queue_stats(posts: list[dict[str, Any]], platform: str) -> dict[str, Any]:
    pending = [p for p in posts if p.get("platform") == platform and p.get("status") == "pending"]
    published = [p for p in posts if p.get("platform") == platform and p.get("status") == "published"]
    pending.sort(key=lambda p: p.get("scheduled_at") or "")
    return {
        "pending": len(pending),
        "published": len(published),
        "next_pending": pending[0]["id"] if pending else None,
    }


def get_status(tenant_id: str = DEFAULT_TENANT, app_id: str | None = None) -> dict[str, Any]:
    from Motor_Tecnico.accio_engine import marketing_app
    from Motor_Tecnico.accio_engine import queue_store
    from Motor_Tecnico.connectors.registry import all_connector_views, load_registry

    aid = _resolve_app_id(tenant_id, app_id)
    paths = _paths(tenant_id)
    queue = load_content_queue_for_app(tenant_id, aid)
    posts = queue.get("posts", [])
    views = all_connector_views(tenant_id)

    content_queue: dict[str, Any] = {"tenant_id": tenant_id, "app_id": aid}
    for view in views:
        pid = view["id"]
        platform = view["platform"]
        stats = _platform_queue_stats(posts, platform)
        content_queue[f"{pid}_pending"] = stats["pending"]
        content_queue[f"{pid}_published"] = stats["published"]
        content_queue[f"{pid}_next"] = stats["next_pending"]
        if platform == "linkedin":
            content_queue["linkedin_pending"] = stats["pending"]
            content_queue["linkedin_published"] = stats["published"]
            content_queue["next_pending"] = stats["next_pending"]
        if platform == "facebook":
            content_queue["facebook_pending"] = stats["pending"]
            content_queue["facebook_published"] = stats["published"]
            content_queue["facebook_next"] = stats["next_pending"]
        if platform == "instagram":
            content_queue["instagram_pending"] = stats["pending"]
            content_queue["instagram_published"] = stats["published"]
            content_queue["instagram_next"] = stats["next_pending"]

    csv_path = BASE_DIR / "leads_prospeccion.csv"
    lead_rows = 0
    if csv_path.exists():
        lead_rows = max(0, sum(1 for _ in csv_path.open()) - 1)

    registry = load_registry(tenant_id)
    return {
        "engine": "accio_marketing_engine",
        "version": 3,
        "tenant_id": tenant_id,
        "app_id": aid,
        "default_app_id": marketing_app.default_app_id(tenant_id),
        "apps_count": len(marketing_app.list_apps(tenant_id)),
        "apps": [a.to_dict() for a in marketing_app.list_apps(tenant_id)],
        "strategy": registry.get("strategy"),
        "time_panama": datetime.now(PANAMA).isoformat(),
        "content_queue": content_queue,
        "connectors": views,
        "prospection_csv_rows": lead_rows,
        "orders_pending": len(queue_store.list_orders(status="pending", tenant_id=tenant_id)),
        "state": queue_store.load_state(tenant_id),
        "paths": {k: str(v) for k, v in paths.items()},
    }


def _action_handlers(tenant_id: str) -> dict:
    def _app(p: dict) -> str | None:
        return p.get("app_id") or None

    return {
        "run_pipeline": lambda p: run_pipeline(tenant_id),
        "publish_linkedin": lambda p: publish_linkedin(
            force=bool(p.get("force")),
            dry_run=bool(p.get("dry_run")),
            tenant_id=tenant_id,
            app_id=_app(p),
        ),
        "publish_facebook": lambda p: publish_meta(
            platform="facebook",
            force=bool(p.get("force")),
            dry_run=bool(p.get("dry_run")),
            tenant_id=tenant_id,
            app_id=_app(p),
        ),
        "publish_instagram": lambda p: publish_meta(
            platform="instagram",
            force=bool(p.get("force")),
            dry_run=bool(p.get("dry_run")),
            tenant_id=tenant_id,
            app_id=_app(p),
        ),
        "publish_meta": lambda p: publish_meta(
            platform=str(p.get("platform", "all")),
            force=bool(p.get("force")),
            dry_run=bool(p.get("dry_run")),
            tenant_id=tenant_id,
            app_id=_app(p),
        ),
        "publish_channel": lambda p: publish_channel(
            connector_id=str(p.get("connector") or p.get("platform", "")),
            force=bool(p.get("force")),
            dry_run=bool(p.get("dry_run")),
            tenant_id=tenant_id,
            app_id=_app(p),
        ),
        "enqueue_post": lambda p: {"post": enqueue_post(p["post"], tenant_id, app_id=_app(p))},
        "enqueue_posts": lambda p: enqueue_posts(p.get("posts", []), tenant_id),
        "set_calendar": lambda p: set_calendar(p.get("calendar", p), tenant_id),
    }


ACTIONS = {
    "run_pipeline",
    "publish_linkedin",
    "publish_facebook",
    "publish_instagram",
    "publish_meta",
    "publish_channel",
    "enqueue_post",
    "enqueue_posts",
    "set_calendar",
}


def execute_action(action: str, params: dict[str, Any] | None = None, tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    params = params or {}
    handlers = _action_handlers(tenant_id)
    handler = handlers.get(action)
    if not handler:
        raise ValueError(f"Accion desconocida: {action}. Validas: {', '.join(sorted(ACTIONS))}")
    return handler(params)
