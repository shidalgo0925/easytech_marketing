"""Brand / Marca schema — M3."""

_BRANDS_DDL = """
CREATE TABLE IF NOT EXISTS brands (
  tenant_id           TEXT NOT NULL,
  brand_id            TEXT NOT NULL,
  company_id          TEXT NOT NULL,
  slug                TEXT NOT NULL,
  name                TEXT NOT NULL,
  description         TEXT,
  tone                TEXT,
  target_audience     TEXT,
  logo_url            TEXT,
  brand_colors_json   TEXT,
  status              TEXT NOT NULL DEFAULT 'active',
  is_default          INTEGER NOT NULL DEFAULT 0,
  legacy_app_id       TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  PRIMARY KEY (tenant_id, brand_id),
  UNIQUE (tenant_id, slug),
  UNIQUE (tenant_id, legacy_app_id)
);

CREATE INDEX IF NOT EXISTS idx_brands_tenant_status
  ON brands(tenant_id, status);
"""
