#!/usr/bin/env python3
"""Utilidades compartidas de cola de publicacion."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent.parent
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"
PANAMA = ZoneInfo("America/Panama")


def load_queue() -> dict[str, Any]:
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def save_queue(data: dict[str, Any]) -> None:
    QUEUE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_scheduled(value: str) -> datetime:
    return datetime.fromisoformat(value)


def pick_next_post(queue: dict[str, Any], platform: str, force: bool = False) -> dict[str, Any] | None:
    now = datetime.now(PANAMA)
    candidates = []
    for post in queue.get("posts", []):
        if post.get("platform") != platform:
            continue
        if post.get("status") != "pending":
            continue
        scheduled = parse_scheduled(post["scheduled_at"])
        if force or scheduled <= now:
            candidates.append((scheduled, post))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def append_log(log_rel: str, entry: dict[str, Any]) -> None:
    path = BASE_DIR / log_rel
    path.parent.mkdir(parents=True, exist_ok=True)
    logs: list = []
    if path.exists():
        logs = json.loads(path.read_text(encoding="utf-8"))
    logs.append(entry)
    path.write_text(json.dumps(logs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def mark_published(queue: dict[str, Any], post_id: str, remote_id: str, platform: str) -> None:
    for item in queue.get("posts", []):
        if item.get("id") != post_id:
            continue
        item["status"] = "published"
        item["published_at"] = datetime.now(PANAMA).isoformat()
        item[f"{platform}_post_id"] = remote_id
        break
    save_queue(queue)
