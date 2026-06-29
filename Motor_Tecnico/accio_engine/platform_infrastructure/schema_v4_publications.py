"""Publications schema — M4."""

_PUBLICATIONS_DDL = """
CREATE TABLE IF NOT EXISTS publications (
  tenant_id           TEXT NOT NULL,
  publication_id      TEXT NOT NULL,
  brand_id            TEXT NOT NULL,
  channel             TEXT NOT NULL,
  title               TEXT,
  body                TEXT NOT NULL,
  status              TEXT NOT NULL DEFAULT 'scheduled',
  scheduled_at        TEXT,
  published_at        TEXT,
  external_post_id    TEXT,
  flyer_ref           TEXT,
  campaign_id         TEXT,
  legacy_queue_id     TEXT,
  payload_json        TEXT,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, publication_id),
  UNIQUE (tenant_id, brand_id, legacy_queue_id)
);

CREATE INDEX IF NOT EXISTS idx_publications_queue
  ON publications(tenant_id, brand_id, status, scheduled_at);
"""
