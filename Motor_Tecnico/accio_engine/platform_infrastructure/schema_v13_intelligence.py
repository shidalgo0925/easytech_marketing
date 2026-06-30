"""Apply schema v13 with safe ALTER for existing databases."""

from __future__ import annotations

import sqlite3


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def apply_schema_v13(conn: sqlite3.Connection) -> None:
    if not _has_column(conn, "opportunities", "score"):
        conn.execute("ALTER TABLE opportunities ADD COLUMN score REAL NOT NULL DEFAULT 0")
    if not _has_column(conn, "opportunities", "reasoning_json"):
        conn.execute("ALTER TABLE opportunities ADD COLUMN reasoning_json TEXT")
    if not _has_column(conn, "recommendations", "explain_json"):
        conn.execute("ALTER TABLE recommendations ADD COLUMN explain_json TEXT")
    if not _has_column(conn, "recommendations", "composed_json"):
        conn.execute("ALTER TABLE recommendations ADD COLUMN composed_json TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(tenant_id, status, score DESC)"
    )
