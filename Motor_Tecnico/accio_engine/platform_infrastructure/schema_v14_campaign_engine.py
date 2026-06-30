"""Schema v14 — Campaign Engine tables and campaign extensions."""

from __future__ import annotations

import sqlite3


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r[1] == column for r in rows)


def _add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    if not _has_column(conn, table, column):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def apply_schema_v14(conn: sqlite3.Connection) -> None:
    for col, defn in (
        ("recommendation_id", "TEXT"),
        ("opportunity_id", "TEXT"),
        ("description", "TEXT"),
        ("target_audience", "TEXT"),
        ("value_proposition", "TEXT"),
        ("call_to_action", "TEXT"),
        ("priority", "TEXT"),
        ("owner", "TEXT"),
        ("start_date", "TEXT"),
        ("end_date", "TEXT"),
        ("budget", "REAL"),
        ("estimated_reach", "INTEGER"),
        ("estimated_leads", "INTEGER"),
        ("estimated_conversion", "REAL"),
        ("campaign_type", "TEXT"),
        ("frequency", "TEXT"),
        ("channels_json", "TEXT"),
        ("kpis_json", "TEXT"),
        ("explain_json", "TEXT"),
        ("llm_enrichment_json", "TEXT"),
        ("llm_skipped", "INTEGER NOT NULL DEFAULT 0"),
        ("planner_version", "TEXT"),
        ("builder_version", "TEXT"),
        ("origin_score", "REAL"),
    ):
        _add_column(conn, "campaigns", col, defn)

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS campaign_channels (
          tenant_id   TEXT NOT NULL,
          campaign_id TEXT NOT NULL,
          channel     TEXT NOT NULL,
          role        TEXT NOT NULL DEFAULT 'primary',
          config_json TEXT,
          PRIMARY KEY (tenant_id, campaign_id, channel)
        );

        CREATE INDEX IF NOT EXISTS idx_campaign_channels_tenant
          ON campaign_channels(tenant_id, campaign_id);

        CREATE TABLE IF NOT EXISTS campaign_kpis (
          tenant_id     TEXT NOT NULL,
          campaign_id   TEXT NOT NULL,
          kpi_id        TEXT NOT NULL,
          name          TEXT NOT NULL,
          target_value  REAL,
          unit          TEXT,
          PRIMARY KEY (tenant_id, campaign_id, kpi_id)
        );

        CREATE INDEX IF NOT EXISTS idx_campaign_kpis_tenant
          ON campaign_kpis(tenant_id, campaign_id);

        CREATE TABLE IF NOT EXISTS campaign_history (
          history_id    TEXT PRIMARY KEY,
          tenant_id     TEXT NOT NULL,
          campaign_id   TEXT NOT NULL,
          event_type    TEXT NOT NULL,
          actor_id      TEXT,
          payload_json  TEXT,
          created_at    TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_campaign_history_campaign
          ON campaign_history(tenant_id, campaign_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_campaigns_tenant_status
          ON campaigns(tenant_id, status);

        CREATE INDEX IF NOT EXISTS idx_campaigns_recommendation
          ON campaigns(tenant_id, recommendation_id);
        """
    )
