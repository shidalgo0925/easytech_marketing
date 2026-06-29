#!/usr/bin/env python3
"""Bitácora de conversaciones y órdenes pendientes del Asistente IA."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import resolve_tenant

AUDIT_FILE = "assistant_audit.jsonl"
ORDERS_FILE = "assistant_orders.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tenant_root(tenant_id: str) -> Path:
    return resolve_tenant(tenant_id).root


def _audit_path(tenant_id: str) -> Path:
    return _tenant_root(tenant_id) / AUDIT_FILE


def _orders_path(tenant_id: str) -> Path:
    return _tenant_root(tenant_id) / ORDERS_FILE


def record_audit(
    tenant_id: str,
    *,
    user: str,
    app_id: str,
    prompt: str,
    response: str,
    actions: list[dict[str, Any]] | None = None,
    mode: str = "suggestion",
    model: str = "rules",
    cost_estimate: float | None = None,
    context_view: str = "",
) -> dict[str, Any]:
    entry = {
        "id": f"audit_{uuid.uuid4().hex[:12]}",
        "at": _utc_now(),
        "user": user,
        "tenant_id": tenant_id,
        "app_id": app_id,
        "prompt": prompt,
        "response": response,
        "actions": actions or [],
        "mode": mode,
        "model": model,
        "cost_estimate": cost_estimate,
        "context_view": context_view,
        "status": "completed",
    }
    path = _audit_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def list_audit(tenant_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    path = _audit_path(tenant_id)
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    items = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(items))


def load_orders(tenant_id: str) -> dict[str, Any]:
    path = _orders_path(tenant_id)
    if not path.is_file():
        return {"version": 1, "orders": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_orders(data: dict[str, Any], tenant_id: str) -> None:
    path = _orders_path(tenant_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def create_order(
    tenant_id: str,
    *,
    app_id: str,
    action_type: str,
    title: str,
    channel: str = "linkedin",
    count: int = 1,
    preview: list[dict[str, Any]] | None = None,
    payload: dict[str, Any] | None = None,
    prompt: str = "",
    user: str = "",
    suggested_at: str = "",
) -> dict[str, Any]:
    order = {
        "id": f"aiord_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "app_id": app_id,
        "action_type": action_type,
        "title": title,
        "channel": channel,
        "count": count,
        "preview": preview or [],
        "payload": payload or {},
        "prompt": prompt,
        "user": user,
        "suggested_at": suggested_at or _utc_now(),
        "status": "pending_approval",
        "created_at": _utc_now(),
    }
    data = load_orders(tenant_id)
    data.setdefault("orders", []).append(order)
    save_orders(data, tenant_id)
    return order


def get_order(tenant_id: str, order_id: str) -> dict[str, Any] | None:
    for order in load_orders(tenant_id).get("orders", []):
        if order.get("id") == order_id:
            return order
    return None


def update_order_status(tenant_id: str, order_id: str, status: str, *, result: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_orders(tenant_id)
    for order in data.get("orders", []):
        if order.get("id") != order_id:
            continue
        order["status"] = status
        order["resolved_at"] = _utc_now()
        if result:
            order["result"] = result
        save_orders(data, tenant_id)
        return order
    raise ValueError(f"Orden no encontrada: {order_id}")


def list_pending_orders(tenant_id: str, app_id: str | None = None) -> list[dict[str, Any]]:
    items = [o for o in load_orders(tenant_id).get("orders", []) if o.get("status") == "pending_approval"]
    if app_id:
        items = [o for o in items if o.get("app_id") == app_id]
    return sorted(items, key=lambda x: x.get("created_at") or "", reverse=True)


def list_all_pending_orders(tenant_id: str) -> list[dict[str, Any]]:
    return list_pending_orders(tenant_id, app_id=None)
