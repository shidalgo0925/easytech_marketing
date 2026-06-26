#!/usr/bin/env python3
"""Carga y evaluacion del registro de conectores (multi-tenant)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _paths(tenant_id: str) -> dict[str, Path]:
    return effective_paths(resolve_tenant(tenant_id))


def load_registry(tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    path = _paths(tenant_id)["connectors"]
    return json.loads(path.read_text(encoding="utf-8"))


def list_connectors(enabled_only: bool = True, tenant_id: str = DEFAULT_TENANT) -> list[dict[str, Any]]:
    items = load_registry(tenant_id).get("connectors", [])
    if enabled_only:
        items = [c for c in items if c.get("enabled", True)]
    return items


def get_connector(connector_id: str, tenant_id: str = DEFAULT_TENANT) -> dict[str, Any] | None:
    for item in list_connectors(enabled_only=False, tenant_id=tenant_id):
        if item.get("id") == connector_id or item.get("platform") == connector_id:
            return item
    return None


def _env_or_secret(tenant_id: str, env_key: str) -> str:
    from Motor_Tecnico.accio_engine import tenant_secrets

    val = tenant_secrets.connector_env_value(tenant_id, env_key)
    if val:
        return val
    if tenant_id == DEFAULT_TENANT:
        return os.getenv(env_key, "").strip()
    return ""


def is_configured(connector: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> bool:
    if connector.get("implementation") == "stub":
        return False
    required = connector.get("env_required") or []
    return all(_env_or_secret(tenant_id, key) for key in required)


def platform_stats(platform: str, tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    queue_path = _paths(tenant_id)["content_queue"]
    if not queue_path.exists():
        return {"pending": 0, "published": 0, "next_pending": None}
    posts = json.loads(queue_path.read_text(encoding="utf-8")).get("posts", [])
    pending = [p for p in posts if p.get("platform") == platform and p.get("status") == "pending"]
    published = [p for p in posts if p.get("platform") == platform and p.get("status") == "published"]
    pending.sort(key=lambda p: p.get("scheduled_at") or "")
    return {
        "pending": len(pending),
        "published": len(published),
        "next_pending": pending[0]["id"] if pending else None,
    }


def connector_status(connector: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> str:
    impl = connector.get("implementation", "stub")
    if impl == "stub":
        return "stub"
    if is_configured(connector, tenant_id):
        return "active"
    return "needs_auth"


def connector_view(connector: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    stats = platform_stats(connector["platform"], tenant_id)
    status = connector_status(connector, tenant_id)
    oauth = connector.get("oauth") or {}
    missing_env = [
        key for key in (connector.get("env_required") or []) if not _env_or_secret(tenant_id, key)
    ]
    return {
        "id": connector["id"],
        "name": connector["name"],
        "phase": connector.get("phase"),
        "platform": connector["platform"],
        "implementation": connector.get("implementation", "stub"),
        "configured": is_configured(connector, tenant_id),
        "status": status,
        "pending": stats["pending"],
        "published": stats["published"],
        "next": stats["next_pending"],
        "auth_url": oauth.get("url"),
        "note": oauth.get("note") or connector.get("docs"),
        "missing_env": missing_env,
        "log_file": connector.get("log_file"),
        "docs": connector.get("docs"),
        "tenant_id": tenant_id,
    }


def all_connector_views(tenant_id: str = DEFAULT_TENANT) -> list[dict[str, Any]]:
    return [connector_view(c, tenant_id) for c in list_connectors(tenant_id=tenant_id)]
