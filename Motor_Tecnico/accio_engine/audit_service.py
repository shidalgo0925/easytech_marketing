#!/usr/bin/env python3
"""Auditoría centralizada (auth, settings, publish)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIT_PATH = BASE_DIR / "Marketing" / "tenants" / ".secrets" / "audit.log"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    tenant_id: str,
    action: str,
    *,
    actor: str = "system",
    category: str = "general",
    success: bool = True,
    detail: dict[str, Any] | None = None,
) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": _utc_now(),
        "tenant_id": tenant_id,
        "category": category,
        "action": action,
        "actor": actor,
        "success": success,
        "detail": detail or {},
    }
    with AUDIT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_events(tenant_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    if not AUDIT_PATH.is_file():
        return []
    lines = AUDIT_PATH.read_text(encoding="utf-8").strip().splitlines()
    events: list[dict[str, Any]] = []
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if tenant_id and row.get("tenant_id") != tenant_id:
            continue
        events.append(row)
        if len(events) >= limit:
            break
    return events
