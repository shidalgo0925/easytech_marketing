#!/usr/bin/env python3
"""Carga y evaluacion del registro de conectores."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = BASE_DIR / "Marketing" / "accio" / "connectors.json"
QUEUE_PATH = BASE_DIR / "Marketing" / "content_queue.json"


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def list_connectors(enabled_only: bool = True) -> list[dict[str, Any]]:
    items = load_registry().get("connectors", [])
    if enabled_only:
        items = [c for c in items if c.get("enabled", True)]
    return items


def get_connector(connector_id: str) -> dict[str, Any] | None:
    for item in list_connectors(enabled_only=False):
        if item.get("id") == connector_id or item.get("platform") == connector_id:
            return item
    return None


def is_configured(connector: dict[str, Any]) -> bool:
    if connector.get("implementation") == "stub":
        return False
    required = connector.get("env_required") or []
    return all(os.getenv(key, "").strip() for key in required)


def platform_stats(platform: str) -> dict[str, Any]:
    if not QUEUE_PATH.exists():
        return {"pending": 0, "published": 0, "next_pending": None}
    posts = json.loads(QUEUE_PATH.read_text(encoding="utf-8")).get("posts", [])
    pending = [p for p in posts if p.get("platform") == platform and p.get("status") == "pending"]
    published = [p for p in posts if p.get("platform") == platform and p.get("status") == "published"]
    pending.sort(key=lambda p: p.get("scheduled_at") or "")
    return {
        "pending": len(pending),
        "published": len(published),
        "next_pending": pending[0]["id"] if pending else None,
    }


def connector_status(connector: dict[str, Any]) -> str:
    impl = connector.get("implementation", "stub")
    stats = platform_stats(connector["platform"])
    if impl == "stub":
        return "stub"
    if is_configured(connector):
        return "active"
    return "needs_auth"


def connector_view(connector: dict[str, Any]) -> dict[str, Any]:
    stats = platform_stats(connector["platform"])
    status = connector_status(connector)
    oauth = connector.get("oauth") or {}
    missing_env = [
        key for key in (connector.get("env_required") or []) if not os.getenv(key, "").strip()
    ]
    return {
        "id": connector["id"],
        "name": connector["name"],
        "phase": connector.get("phase"),
        "platform": connector["platform"],
        "implementation": connector.get("implementation", "stub"),
        "configured": is_configured(connector),
        "status": status,
        "pending": stats["pending"],
        "published": stats["published"],
        "next": stats["next_pending"],
        "auth_url": oauth.get("url"),
        "note": oauth.get("note") or connector.get("docs"),
        "missing_env": missing_env,
        "log_file": connector.get("log_file"),
        "docs": connector.get("docs"),
    }


def all_connector_views() -> list[dict[str, Any]]:
    return [connector_view(c) for c in list_connectors()]
