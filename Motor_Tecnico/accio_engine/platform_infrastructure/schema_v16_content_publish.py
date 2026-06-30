"""Schema v16 — Content Engine publish fields (VS2)."""

from __future__ import annotations

import sqlite3

_V16_COLUMNS = (
    ("approved_by", "TEXT"),
    ("approved_at", "TEXT"),
    ("rejected_reason", "TEXT"),
    ("publish_channel", "TEXT"),
    ("publish_status", "TEXT"),
    ("published_at", "TEXT"),
    ("publish_result_json", "TEXT"),
    ("error_message", "TEXT"),
    ("queue_post_id", "TEXT"),
)


def apply_schema_v16(conn: sqlite3.Connection) -> None:
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(content_pieces)").fetchall()
    }
    for name, col_type in _V16_COLUMNS:
        if name not in existing:
            conn.execute(f"ALTER TABLE content_pieces ADD COLUMN {name} {col_type}")
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_content_pieces_publish
          ON content_pieces(tenant_id, status, publish_channel)
        """
    )
