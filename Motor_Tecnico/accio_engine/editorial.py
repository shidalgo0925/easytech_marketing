#!/usr/bin/env python3
"""Estados editoriales y transiciones para publicaciones EM+Acción."""

from __future__ import annotations

from typing import Any

STATUSES = frozenset(
    {
        "draft",
        "pending_approval",
        "approved",
        "scheduled",
        "published",
        "failed",
        "archived",
    }
)

# Legacy: pending = programado listo para publicar (compat easytech)
LEGACY_PUBLISHABLE = frozenset({"pending"})
PUBLISHABLE = frozenset({"approved", "scheduled"}) | LEGACY_PUBLISHABLE
TERMINAL = frozenset({"published", "archived", "failed"})

TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"pending_approval", "archived", "scheduled"}),
    "pending_approval": frozenset({"approved", "draft", "archived"}),
    "approved": frozenset({"scheduled", "pending_approval", "archived"}),
    "scheduled": frozenset({"approved", "pending_approval", "published", "failed", "archived"}),
    "published": frozenset({"archived"}),
    "failed": frozenset({"draft", "scheduled", "archived"}),
    "archived": frozenset({"draft"}),
    "pending": frozenset({"scheduled", "approved", "published", "failed", "archived"}),
}


def normalize_status(status: str | None, *, default: str = "scheduled") -> str:
    raw = (status or default).strip().lower()
    if raw in STATUSES or raw == "pending":
        return raw
    return default


def is_publishable(status: str | None) -> bool:
    return normalize_status(status) in PUBLISHABLE


def can_transition(current: str | None, new: str) -> bool:
    cur = normalize_status(current, default="draft")
    nxt = normalize_status(new)
    allowed = TRANSITIONS.get(cur, frozenset())
    return nxt in allowed or nxt == cur


def apply_status(post: dict[str, Any], new_status: str) -> dict[str, Any]:
    cur = normalize_status(post.get("status"))
    nxt = normalize_status(new_status)
    if not can_transition(cur, nxt):
        raise ValueError(f"Transición no permitida: {cur} → {nxt}")
    post["status"] = nxt
    return post


def editorial_label(status: str | None) -> str:
    labels = {
        "draft": "Borrador",
        "pending_approval": "Pendiente aprobación",
        "approved": "Aprobado",
        "scheduled": "Programado",
        "published": "Publicado",
        "failed": "Fallido",
        "archived": "Archivado",
        "pending": "Programado (legacy)",
    }
    return labels.get(normalize_status(status), normalize_status(status))
