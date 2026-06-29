"""Media assets schema — M8."""

_MEDIA_ASSETS_DDL = """
CREATE TABLE IF NOT EXISTS media_assets (
  tenant_id       TEXT NOT NULL,
  asset_id        TEXT NOT NULL,
  brand_id        TEXT NOT NULL DEFAULT 'default',
  asset_type      TEXT NOT NULL DEFAULT 'flyer',
  uri             TEXT NOT NULL,
  title           TEXT,
  status          TEXT NOT NULL DEFAULT 'available',
  flyer_num       INTEGER,
  payload_json    TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  PRIMARY KEY (tenant_id, asset_id)
);

CREATE INDEX IF NOT EXISTS idx_media_assets_tenant_type
  ON media_assets(tenant_id, asset_type, status);
"""
