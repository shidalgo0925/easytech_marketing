"""SQLite platform database — Marketing OS M0."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "Marketing" / "platform" / "marketing_os.db"

SCHEMA_VERSION = 1

_MEMORY_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS memory_events (
  event_id        TEXT PRIMARY KEY,
  tenant_id       TEXT NOT NULL,
  brand_id        TEXT,
  event_type      TEXT NOT NULL,
  actor_type      TEXT NOT NULL,
  actor_id        TEXT,
  timestamp       TEXT NOT NULL,
  entity_refs_json TEXT NOT NULL,
  payload_json    TEXT,
  summary         TEXT,
  correlation_id  TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_tenant_time
  ON memory_events(tenant_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_memory_tenant_type
  ON memory_events(tenant_id, event_type);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL
);
"""


def get_db_path() -> Path:
    raw = os.environ.get("ACCIO_PLATFORM_DB", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_DB_PATH


def memory_store_mode() -> str:
    """off | sql | dual — default sql after M0."""
    return os.environ.get("ACCIO_MEMORY_STORE", "sql").strip().lower() or "sql"


def memory_sql_enabled() -> bool:
    return memory_store_mode() in {"sql", "dual"}


def get_connection(*, readonly: bool = False) -> sqlite3.Connection:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    uri = f"file:{path}?mode={'ro' if readonly else 'rwc'}"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_schema(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    if own:
        conn = get_connection()
    try:
        conn.executescript(_MEMORY_EVENTS_DDL)
        row = conn.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            (SCHEMA_VERSION,),
        ).fetchone()
        if row is None:
            from datetime import datetime, timezone

            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
            )
        conn.commit()
    finally:
        if own:
            conn.close()
