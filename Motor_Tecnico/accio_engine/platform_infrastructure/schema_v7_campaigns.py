"""Campaigns schema — M7."""

_CAMPAIGNS_DDL = """
CREATE TABLE IF NOT EXISTS campaigns (
  tenant_id       TEXT NOT NULL,
  campaign_id     TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  name            TEXT NOT NULL,
  post_id         TEXT,
  product_ref     TEXT,
  channel         TEXT,
  status          TEXT NOT NULL DEFAULT 'active',
  objective       TEXT,
  start_at        TEXT,
  end_at          TEXT,
  payload_json    TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  PRIMARY KEY (tenant_id, campaign_id),
  UNIQUE (tenant_id, brand_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_campaigns_brand_status
  ON campaigns(tenant_id, brand_id, status);
"""
