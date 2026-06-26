#!/usr/bin/env python3
"""Cola de órdenes Accio (persistente en JSON, por tenant)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, effective_paths, resolve_tenant


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paths(tenant_id: str) -> dict[str, Path]:
    tenant = resolve_tenant(tenant_id)
    return effective_paths(tenant)


def load_orders(tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    path = _paths(tenant_id)["orders"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        data = {"orders": []}
        save_orders(data, tenant_id)
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def save_orders(data: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> None:
    path = _paths(tenant_id)["orders"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state(tenant_id: str = DEFAULT_TENANT) -> dict[str, Any]:
    path = _paths(tenant_id)["state"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        data = {"last_tick": None, "last_actions": {}}
        save_state(data, tenant_id)
        return data
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(data: dict[str, Any], tenant_id: str = DEFAULT_TENANT) -> None:
    path = _paths(tenant_id)["state"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def create_order(
    action: str,
    params: dict | None = None,
    source: str = "accio",
    tenant_id: str = DEFAULT_TENANT,
) -> dict[str, Any]:
    order = {
        "id": f"ord_{uuid.uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "action": action,
        "params": params or {},
        "source": source,
        "status": "pending",
        "created_at": _utc_now(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None,
    }
    data = load_orders(tenant_id)
    data.setdefault("orders", []).append(order)
    save_orders(data, tenant_id)
    return order


def list_orders(status: str | None = None, limit: int = 50, tenant_id: str = DEFAULT_TENANT) -> list[dict[str, Any]]:
    orders = load_orders(tenant_id).get("orders", [])
    if status:
        orders = [o for o in orders if o.get("status") == status]
    return list(reversed(orders[-limit:]))


def get_order(order_id: str, tenant_id: str = DEFAULT_TENANT) -> dict[str, Any] | None:
    for order in load_orders(tenant_id).get("orders", []):
        if order["id"] == order_id:
            return order
    return None


def update_order(order_id: str, tenant_id: str = DEFAULT_TENANT, **fields: Any) -> dict[str, Any] | None:
    data = load_orders(tenant_id)
    for order in data.get("orders", []):
        if order["id"] == order_id:
            order.update(fields)
            save_orders(data, tenant_id)
            return order
    return None


def pending_orders(tenant_id: str = DEFAULT_TENANT) -> list[dict[str, Any]]:
    return [o for o in load_orders(tenant_id).get("orders", []) if o.get("status") == "pending"]
