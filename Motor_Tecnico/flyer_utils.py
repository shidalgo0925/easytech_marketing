#!/usr/bin/env python3
"""Resolucion de rutas de flyers en la cola de publicacion."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FLYERS_DIR = BASE_DIR / "Marketing" / "flyers"


def resolve_flyer_path(post: dict) -> Path | None:
    """Devuelve la ruta local del flyer o None si no existe."""
    flyer = (post.get("flyer") or "").strip()
    if not flyer:
        return None

    name = Path(flyer).name
    candidates = [
        BASE_DIR / "Marketing" / flyer,
        FLYERS_DIR / name,
        BASE_DIR / flyer,
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def flyer_public_url(post: dict, public_base: str) -> str | None:
    path = resolve_flyer_path(post)
    if not path:
        return None
    return f"{public_base.rstrip('/')}/accio/assets/flyers/{path.name}"


def validate_queue_flyers(queue: dict) -> list[dict]:
    """Lista posts pending sin flyer en disco."""
    missing = []
    for post in queue.get("posts", []):
        if post.get("status") != "pending":
            continue
        if not post.get("flyer"):
            missing.append({"id": post.get("id"), "platform": post.get("platform"), "reason": "sin flyer en cola"})
            continue
        if not resolve_flyer_path(post):
            missing.append(
                {
                    "id": post.get("id"),
                    "platform": post.get("platform"),
                    "flyer": post.get("flyer"),
                    "reason": "archivo no encontrado",
                }
            )
    return missing
