#!/usr/bin/env python3
"""Ejecuta acciones del motor Accio sobre componentes existentes."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = BASE_DIR / "venv" / "bin" / "python3"
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"
CALENDAR_PATH = BASE_DIR / "Marketing" / "accio" / "calendar.json"
PANAMA = ZoneInfo("America/Panama")


def _run_script(script: str, *args: str) -> dict[str, Any]:
    cmd = [str(VENV_PYTHON), str(BASE_DIR / "Motor_Tecnico" / script), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(BASE_DIR), timeout=600)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-8000:] if proc.stdout else "",
        "stderr": proc.stderr[-4000:] if proc.stderr else "",
    }


def run_pipeline() -> dict[str, Any]:
    scrape = _run_script("scraper_panama.py")
    if not scrape["ok"]:
        return {"step": "scraper", **scrape}
    sync = _run_script("odoo_sync.py")
    return {"step": "odoo_sync", "scrape": scrape, **sync}


def publish_linkedin(force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    args = []
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    return _run_script("linkedin_publisher.py", *args)


def publish_meta(platform: str = "all", force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    args = [f"--platform={platform}"]
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")
    return _run_script("meta_publisher.py", *args)


def load_content_queue() -> dict[str, Any]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_content_queue(data: dict[str, Any]) -> None:
    QUEUE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def enqueue_post(post: dict[str, Any]) -> dict[str, Any]:
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

    queue = load_content_queue()
    posts = queue.setdefault("posts", [])
    for existing in posts:
        if existing.get("id") == entry["id"]:
            raise ValueError(f"Post id duplicado: {entry['id']}")
    posts.append(entry)
    save_content_queue(queue)
    return entry


def enqueue_posts(posts: list[dict[str, Any]]) -> dict[str, Any]:
    created = []
    errors = []
    for post in posts:
        try:
            created.append(enqueue_post(post))
        except ValueError as exc:
            errors.append({"id": post.get("id"), "error": str(exc)})
    return {"created": created, "errors": errors, "count": len(created)}


def set_calendar(calendar: dict[str, Any]) -> dict[str, Any]:
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(PANAMA).isoformat(),
        **calendar,
    }
    CALENDAR_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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


def get_status() -> dict[str, Any]:
    queue = load_content_queue()
    posts = queue.get("posts", [])
    li = _platform_queue_stats(posts, "linkedin")
    fb = _platform_queue_stats(posts, "facebook")
    ig = _platform_queue_stats(posts, "instagram")

    csv_path = BASE_DIR / "leads_prospeccion.csv"
    lead_rows = 0
    if csv_path.exists():
        lead_rows = max(0, sum(1 for _ in csv_path.open()) - 1)

    from Motor_Tecnico.accio_engine.queue_store import list_orders, load_state  # noqa: PLC0415

    return {
        "engine": "accio_marketing_engine",
        "version": 1,
        "time_panama": datetime.now(PANAMA).isoformat(),
        "content_queue": {
            "linkedin_pending": li["pending"],
            "linkedin_published": li["published"],
            "next_pending": li["next_pending"],
            "facebook_pending": fb["pending"],
            "facebook_published": fb["published"],
            "facebook_next": fb["next_pending"],
            "instagram_pending": ig["pending"],
            "instagram_published": ig["published"],
            "instagram_next": ig["next_pending"],
        },
        "prospection_csv_rows": lead_rows,
        "orders_pending": len(list_orders(status="pending")),
        "state": load_state(),
        "paths": {
            "content_queue": str(QUEUE_PATH),
            "flyers_manifest": str(BASE_DIR / "Marketing" / "flyers" / "manifest.json"),
            "calendar": str(CALENDAR_PATH),
            "meta_publish_log": str(BASE_DIR / "Marketing" / "meta_publish_log.json"),
        },
    }


ACTIONS = {
    "run_pipeline": lambda p: run_pipeline(),
    "publish_linkedin": lambda p: publish_linkedin(
        force=bool(p.get("force")), dry_run=bool(p.get("dry_run"))
    ),
    "publish_facebook": lambda p: publish_meta(
        platform="facebook", force=bool(p.get("force")), dry_run=bool(p.get("dry_run"))
    ),
    "publish_instagram": lambda p: publish_meta(
        platform="instagram", force=bool(p.get("force")), dry_run=bool(p.get("dry_run"))
    ),
    "publish_meta": lambda p: publish_meta(
        platform=str(p.get("platform", "all")),
        force=bool(p.get("force")),
        dry_run=bool(p.get("dry_run")),
    ),
    "enqueue_post": lambda p: {"post": enqueue_post(p["post"])},
    "enqueue_posts": lambda p: enqueue_posts(p.get("posts", [])),
    "set_calendar": lambda p: set_calendar(p.get("calendar", p)),
}


def execute_action(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    handler = ACTIONS.get(action)
    if not handler:
        raise ValueError(f"Accion desconocida: {action}. Validas: {', '.join(sorted(ACTIONS))}")
    return handler(params)
