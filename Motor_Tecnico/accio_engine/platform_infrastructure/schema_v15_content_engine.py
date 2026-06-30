"""Schema v15 — Content Engine."""

from __future__ import annotations

import sqlite3


_CONTENT_PIECES_DDL = """
CREATE TABLE IF NOT EXISTS content_pieces (
  tenant_id           TEXT NOT NULL,
  content_id          TEXT NOT NULL,
  campaign_id         TEXT,
  recommendation_id   TEXT,
  brand_id            TEXT NOT NULL,
  title               TEXT NOT NULL,
  format              TEXT NOT NULL DEFAULT 'post',
  channel             TEXT NOT NULL DEFAULT 'linkedin',
  content_type        TEXT NOT NULL DEFAULT 'valor',
  status              TEXT NOT NULL DEFAULT 'draft',
  headline            TEXT,
  body                TEXT,
  call_to_action      TEXT,
  hashtags_json       TEXT,
  flyer_ref           TEXT,
  objective           TEXT,
  explain_json        TEXT,
  llm_enrichment_json TEXT,
  llm_skipped         INTEGER NOT NULL DEFAULT 0,
  planner_version     TEXT,
  builder_version     TEXT,
  payload_json        TEXT,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, content_id)
);

CREATE INDEX IF NOT EXISTS idx_content_pieces_campaign
  ON content_pieces(tenant_id, campaign_id);

CREATE INDEX IF NOT EXISTS idx_content_pieces_status
  ON content_pieces(tenant_id, status);

CREATE TABLE IF NOT EXISTS content_variants (
  tenant_id     TEXT NOT NULL,
  content_id    TEXT NOT NULL,
  variant_id    TEXT NOT NULL,
  label         TEXT NOT NULL,
  headline      TEXT,
  body          TEXT,
  payload_json  TEXT,
  PRIMARY KEY (tenant_id, content_id, variant_id)
);

CREATE TABLE IF NOT EXISTS content_history (
  history_id    TEXT PRIMARY KEY,
  tenant_id     TEXT NOT NULL,
  content_id    TEXT NOT NULL,
  event_type    TEXT NOT NULL,
  actor_id      TEXT,
  payload_json  TEXT,
  created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_content_history_piece
  ON content_history(tenant_id, content_id, created_at DESC);
"""


def apply_schema_v15(conn: sqlite3.Connection) -> None:
    conn.executescript(_CONTENT_PIECES_DDL)
