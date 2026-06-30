#!/usr/bin/env python3
"""Verificación Bloque 1 — marketing_os.db + stores dual."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.platform_infrastructure.db import (  # noqa: E402
    asset_store_mode,
    brain_store_mode,
    brand_store_mode,
    campaign_store_mode,
    ensure_schema,
    get_connection,
    get_db_path,
    knowledge_store_mode,
    lead_store_mode,
    memory_sql_enabled,
    product_store_mode,
    publication_store_mode,
)


def _count(table: str) -> int:
    conn = get_connection()
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return -1
    finally:
        conn.close()


def main() -> int:
    errors: list[str] = []
    db_path = get_db_path()
    if not db_path.is_file():
        errors.append(f"BD no encontrada: {db_path}")

    ensure_schema()
    conn = get_connection()
    try:
        vers = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
    finally:
        conn.close()

    if not vers:
        errors.append("schema_migrations vacío")

    stores = {
        "ACCIO_MEMORY_STORE": "sql" if memory_sql_enabled() else "off",
        "ACCIO_BRAIN_STORE": brain_store_mode(),
        "ACCIO_BRAND_STORE": brand_store_mode(),
        "ACCIO_PUBLICATION_STORE": publication_store_mode(),
        "ACCIO_PRODUCT_STORE": product_store_mode(),
        "ACCIO_KNOWLEDGE_STORE": knowledge_store_mode(),
        "ACCIO_CAMPAIGN_STORE": campaign_store_mode(),
        "ACCIO_ASSET_STORE": asset_store_mode(),
        "ACCIO_LEAD_STORE": lead_store_mode(),
    }

    print(f"DB: {db_path}")
    print(f"Schema versions: {vers[-5:]} (max {max(vers) if vers else 0})")
    print("Stores:", stores)

    for name, mode in stores.items():
        if name == "ACCIO_MEMORY_STORE":
            if mode != "sql":
                errors.append(f"{name} debe ser sql en prod (actual: {mode})")
        elif mode not in {"dual", "sql"}:
            errors.append(f"{name} debe ser dual o sql en prod (actual: {mode})")

    tables = {
        "memory_events": 1,
        "company_profiles": 1,
        "brands": 1,
        "publications": 1,
        "products": 1,
        "knowledge_articles": 1,
        "campaigns": 0,
        "media_assets": 1,
    }
    print("Counts:")
    for table, min_rows in tables.items():
        n = _count(table)
        print(f"  {table}: {n}")
        if n < min_rows:
            errors.append(f"{table}: esperado >= {min_rows}, tiene {n}")

    # Dual-read smoke: publication facade
    try:
        from Motor_Tecnico.accio_engine import executor

        q = executor.load_content_queue("easytech")
        posts = len(q.get("posts", []))
        print(f"  content_queue easytech (facade): {posts} posts")
        if posts < 1:
            errors.append("content_queue easytech vacío vía facade")
    except Exception as exc:
        errors.append(f"facade load_content_queue: {exc}")

    env_prod = Path(os.environ.get("ACCIO_ROOT", str(BASE))) / "deploy" / "secrets" / ".env.prod"
    if not env_prod.is_file():
        errors.append(f"Falta {env_prod} (systemd prod)")

    if errors:
        print("\nFALLOS:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\nOK — Bloque 1 verificación pasada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
