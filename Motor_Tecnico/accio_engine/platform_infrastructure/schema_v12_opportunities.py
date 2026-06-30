"""Opportunities schema — Opportunity Engine F1."""

_OPPORTUNITIES_DDL = """
CREATE TABLE IF NOT EXISTS opportunities (
  tenant_id         TEXT NOT NULL,
  opportunity_id    TEXT NOT NULL,
  signal_key        TEXT NOT NULL,
  signal_type       TEXT NOT NULL,
  brand_id          TEXT,
  title             TEXT NOT NULL,
  description       TEXT,
  sector            TEXT,
  need              TEXT,
  product_slug      TEXT,
  channel           TEXT,
  landing_url       TEXT,
  priority          TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'detected',
  confidence        REAL NOT NULL DEFAULT 1.0,
  source            TEXT NOT NULL,
  payload_json      TEXT,
  detected_at       TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  PRIMARY KEY (tenant_id, opportunity_id),
  UNIQUE (tenant_id, signal_key)
);

CREATE INDEX IF NOT EXISTS idx_opportunities_inbox
  ON opportunities(tenant_id, status, priority, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_opportunities_brand
  ON opportunities(tenant_id, brand_id, status);
"""
