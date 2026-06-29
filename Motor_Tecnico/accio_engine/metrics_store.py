#!/usr/bin/env python3
"""Métricas agregables por tenant, app, campaña, canal y publicación."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def metrics_path(tenant_id: str, app_id: str | None = None) -> Path:
    paths = marketing_app.effective_app_paths(tenant_id, app_id)
    root = paths["app_root"]
    metrics_dir = root / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    return metrics_dir / "events.jsonl"


def record_event(
    tenant_id: str,
    event_type: str,
    *,
    app_id: str | None = None,
    campaign_id: str = "",
    channel: str = "",
    post_id: str = "",
    lead_id: str = "",
    value: int | float = 1,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    entry = {
        "at": _utc_now(),
        "tenant_id": tenant_id,
        "app_id": aid,
        "event_type": event_type,
        "campaign_id": campaign_id,
        "channel": channel,
        "post_id": post_id,
        "lead_id": lead_id,
        "value": value,
        "meta": meta or {},
    }
    path = metrics_path(tenant_id, aid)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def _load_events(tenant_id: str, app_id: str | None = None) -> list[dict[str, Any]]:
    path = metrics_path(tenant_id, app_id)
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def aggregate(
    tenant_id: str,
    app_id: str | None = None,
    *,
    group_by: str = "event_type",
) -> list[dict[str, Any]]:
    counts: dict[str, float] = {}
    for ev in _load_events(tenant_id, app_id):
        key = str(ev.get(group_by) or "unknown")
        counts[key] = counts.get(key, 0) + float(ev.get("value") or 1)
    return [{"key": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


def summary_for_dashboard(tenant_id: str, app_id: str | None = None) -> dict[str, Any]:
    events = _load_events(tenant_id, app_id)
    by_type = aggregate(tenant_id, app_id, group_by="event_type")
    by_channel = aggregate(tenant_id, app_id, group_by="channel")
    return {
        "events_total": len(events),
        "by_event_type": by_type,
        "by_channel": by_channel,
    }
