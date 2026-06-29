"""Products schema — M5."""

_PRODUCTS_DDL = """
CREATE TABLE IF NOT EXISTS products (
  tenant_id       TEXT NOT NULL,
  product_id      TEXT NOT NULL,
  brand_id        TEXT NOT NULL,
  slug            TEXT NOT NULL,
  name            TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'active',
  landing_path    TEXT,
  cta             TEXT,
  payload_json    TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  PRIMARY KEY (tenant_id, product_id),
  UNIQUE (tenant_id, brand_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_products_tenant_brand
  ON products(tenant_id, brand_id, status);
"""
