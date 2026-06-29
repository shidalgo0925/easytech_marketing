#!/usr/bin/env python3
"""Migración de posts de cola default → colas por app (flyer / producto)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant

# Flyer manifest num → app_id (posts de marca cruzada quedan en default)
FLYER_NUM_TO_APP: dict[int, str] = {
    1: "desarrollo",
    2: "odoo-fe",
    3: "odoo-fe",
    4: "consultoria",
    5: "en1",
    6: "eclassone",
    7: "ethesisone",
    8: "eposone",
    9: "epayroll",
}

# Flyers multi-producto / CTA empresa → default
DEFAULT_FLYER_NUMS = frozenset({10, 11, 12})

_FLYER_HINTS: list[tuple[str, str]] = [
    ("eposone", "eposone"),
    ("epayroll", "epayroll"),
    ("eclassone", "eclassone"),
    ("ethesisone", "ethesisone"),
    ("en1", "en1"),
    ("odoo", "odoo-fe"),
    ("facturacion_electronica", "odoo-fe"),
    ("consultoria", "consultoria"),
    ("desarrollo_software", "desarrollo"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_manifest(tenant_id: str) -> dict[str, Any]:
    path = effective_paths(resolve_tenant(tenant_id))["flyers_manifest"]
    if not path.is_file():
        return {"flyers": []}
    return json.loads(path.read_text(encoding="utf-8"))


def flyer_num_from_post(post: dict[str, Any], manifest: dict[str, Any]) -> int | None:
    if post.get("flyer_num"):
        return int(post["flyer_num"])
    flyer = post.get("flyer") or ""
    match = re.search(r"(\d{2})_", flyer)
    if match:
        return int(match.group(1))
    for item in manifest.get("flyers", []):
        file_name = item.get("file") or ""
        if file_name and file_name in flyer:
            return item.get("num")
    return None


def resolve_app_for_post(
    post: dict[str, Any],
    tenant_id: str,
    manifest: dict[str, Any] | None = None,
) -> str:
    """Devuelve app_id destino; default si es contenido de marca / multi-producto."""
    if post.get("app_id") and post["app_id"] != marketing_app.DEFAULT_APP_ID:
        return marketing_app.normalize_app_id(post["app_id"])

    manifest = manifest or _load_manifest(tenant_id)
    num = flyer_num_from_post(post, manifest)
    if num in DEFAULT_FLYER_NUMS:
        return marketing_app.default_app_id(tenant_id)
    if num and num in FLYER_NUM_TO_APP:
        return FLYER_NUM_TO_APP[num]

    haystack = f"{post.get('id', '')} {post.get('flyer', '')}".lower()
    for hint, app_id in _FLYER_HINTS:
        if hint in haystack:
            return app_id

    return marketing_app.default_app_id(tenant_id)


def _load_queue(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"posts": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_queue(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_default_queue_to_apps(
    tenant_id: str = DEFAULT_TENANT,
    *,
    dry_run: bool = False,
    backup: bool = True,
) -> dict[str, Any]:
    """
    Mueve posts de la cola default del tenant a colas por app según flyer/producto.
    Idempotente: posts ya en su app no se duplican.
    """
    marketing_app.provision_all_apps(tenant_id)
    default_id = marketing_app.default_app_id(tenant_id)
    manifest = _load_manifest(tenant_id)
    default_path = marketing_app.queue_file_path(tenant_id, default_id)
    if not default_path.is_file():
        return {"ok": True, "moved": 0, "kept_default": 0, "by_app": {}, "dry_run": dry_run}

    raw = _load_queue(default_path)
    posts = raw.get("posts", [])
    if not posts:
        return {"ok": True, "moved": 0, "kept_default": 0, "by_app": {}, "dry_run": dry_run}

    if backup and not dry_run:
        backup_path = default_path.with_suffix(f".json.bak.{_utc_now()}")
        shutil.copy2(default_path, backup_path)

    kept_default: list[dict[str, Any]] = []
    by_app: dict[str, list[dict[str, Any]]] = {}
    moved = 0

    for post in posts:
        target = resolve_app_for_post(post, tenant_id, manifest)
        if target == default_id:
            post["app_id"] = default_id
            kept_default.append(post)
            continue
        entry = {**post, "app_id": target}
        by_app.setdefault(target, []).append(entry)
        moved += 1

    result = {
        "ok": True,
        "tenant_id": tenant_id,
        "dry_run": dry_run,
        "moved": moved,
        "kept_default": len(kept_default),
        "by_app": {k: len(v) for k, v in sorted(by_app.items())},
        "backup": str(default_path.with_suffix(f".json.bak.{_utc_now()}")) if backup and not dry_run else None,
    }

    if dry_run:
        result["preview"] = {
            "default_ids": [p["id"] for p in kept_default],
            "app_posts": {k: [p["id"] for p in v] for k, v in by_app.items()},
        }
        return result

    _save_queue(default_path, {**raw, "posts": kept_default})

    for app_id, app_posts in by_app.items():
        qpath = marketing_app.queue_file_path(tenant_id, app_id)
        app_queue = _load_queue(qpath)
        existing_ids = {p.get("id") for p in app_queue.get("posts", [])}
        merged = list(app_queue.get("posts", []))
        for post in app_posts:
            if post["id"] in existing_ids:
                continue
            merged.append(post)
            existing_ids.add(post["id"])
        _save_queue(qpath, {**app_queue, "posts": merged})

    return result
