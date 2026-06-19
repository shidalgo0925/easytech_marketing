#!/usr/bin/env python3
"""Árbol de archivos del proyecto para Accio Work / dashboard."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOTS = ("Marketing", "Motor_Tecnico", "docs", "scripts")
SKIP_DIRS = {"__pycache__", "venv", "archive", "node_modules", ".git"}
MAX_DEPTH = 4


def _walk(rel_root: str, depth: int = 0) -> list[dict]:
    base = BASE_DIR / rel_root
    if not base.is_dir():
        return []
    items: list[dict] = []
    try:
        entries = sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError:
        return items
    for entry in entries:
        if entry.name.startswith(".") and entry.name != ".env.example":
            continue
        if entry.is_dir() and entry.name in SKIP_DIRS:
            continue
        rel = f"{rel_root}/{entry.name}"
        if entry.is_dir():
            node: dict = {"name": entry.name, "path": rel, "type": "dir"}
            if depth < MAX_DEPTH:
                node["children"] = _walk(rel, depth + 1)
            items.append(node)
        else:
            items.append({"name": entry.name, "path": rel, "type": "file", "size": entry.stat().st_size})
    return items


def get_file_tree() -> dict:
    return {
        "project_root": str(BASE_DIR),
        "deliverables": {root: _walk(root) for root in ROOTS},
    }


def read_text_file(rel_path: str, max_bytes: int = 50000) -> dict:
    target = (BASE_DIR / rel_path).resolve()
    if not str(target).startswith(str(BASE_DIR.resolve())):
        raise ValueError("Ruta no permitida")
    if not target.is_file():
        raise FileNotFoundError(rel_path)
    data = target.read_bytes()[:max_bytes]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("No es archivo de texto")
    return {"path": rel_path, "content": text, "truncated": target.stat().st_size > max_bytes}
