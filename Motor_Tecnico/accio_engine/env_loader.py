#!/usr/bin/env python3
"""Carga de variables por entorno ACCIO_ENV (prod | dev | test)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

VALID_ENVS = frozenset({"prod", "dev", "test"})


def load_accio_env(base_dir: Path | None = None) -> str:
    """Carga capas de .env en orden (cada archivo posterior sobrescribe)."""
    base = base_dir or Path(__file__).resolve().parent.parent.parent
    env = os.getenv("ACCIO_ENV", "prod").strip().lower()
    if env not in VALID_ENVS:
        env = "prod"

    layers = [
        base / "deploy" / "secrets" / f".env.{env}",
        base / f".env.{env}",
        base / ".env",
    ]
    seen: set[Path] = set()
    for path in layers:
        resolved = path.resolve()
        if path.is_file() and resolved not in seen:
            load_dotenv(path, override=True)
            seen.add(resolved)

    os.environ["ACCIO_ENV"] = env
    return env
