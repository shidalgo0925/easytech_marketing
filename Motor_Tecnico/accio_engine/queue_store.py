#!/usr/bin/env python3
"""Cola de órdenes Accio (persistente en JSON)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ORDERS_PATH = BASE_DIR / "Marketing" / "accio" / "orders.json"
STATE_PATH = BASE_DIR / "Marketing" / "accio" / "state.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    ORDERS_PATH.parent.mkdir(parents=True, exist_ok=True)


def load_orders() -> dict[str, Any]:
    _ensure_dir()
    if not ORDERS_PATH.exists():
        data = {"orders": []}
        save_orders(data)
        return data
    return json.loads(ORDERS_PATH.read_text(encoding="utf-8"))


def save_orders(data: dict[str, Any]) -> None:
    _ensure_dir()
    ORDERS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state() -> dict[str, Any]:
    _ensure_dir()
    if not STATE_PATH.exists():
        data = {"last_tick": None, "last_actions": {}}
        save_state(data)
        return data
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(data: dict[str, Any]) -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def create_order(action: str, params: dict | None = None, source: str = "accio") -> dict[str, Any]:
    order = {
        "id": f"ord_{uuid.uuid4().hex[:12]}",
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
    data = load_orders()
    data.setdefault("orders", []).append(order)
    save_orders(data)
    return order


def list_orders(status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    orders = load_orders().get("orders", [])
    if status:
        orders = [o for o in orders if o.get("status") == status]
    return list(reversed(orders[-limit:]))


def get_order(order_id: str) -> dict[str, Any] | None:
    for order in load_orders().get("orders", []):
        if order["id"] == order_id:
            return order
    return None


def update_order(order_id: str, **fields: Any) -> dict[str, Any] | None:
    data = load_orders()
    for order in data.get("orders", []):
        if order["id"] == order_id:
            order.update(fields)
            save_orders(data)
            return order
    return None


def pending_orders() -> list[dict[str, Any]]:
    return [o for o in load_orders().get("orders", []) if o.get("status") == "pending"]
