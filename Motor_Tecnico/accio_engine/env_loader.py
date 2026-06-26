#!/usr/bin/env python3
"""Carga de variables por entorno ACCIO_ENV (prod | dev | test)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

VALID_ENVS = frozenset({"prod", "dev", "test"})


def load_accio_env(base_dir: Path | None = None) -> str:
    """Carga el primer .env encontrado según ACCIO_ENV. Devuelve el entorno activo."""
    base = base_dir or Path(__file__).resolve().parent.parent.parent
    env = os.getenv("ACCIO_ENV", "prod").strip().lower()
    if env not in VALID_ENVS:
        env = "prod"

    candidates = [
        base / "deploy" / "secrets" / f".env.{env}",
        base / f".env.{env}",
        base / ".env",
    ]
    loaded = False
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=True)
            loaded = True
            break
    if not loaded and env != "prod":
        load_dotenv(base / ".env", override=True)

    os.environ["ACCIO_ENV"] = env
    return env
