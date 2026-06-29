"""Leads schema — M9."""

_LEADS_DDL = """
CREATE TABLE IF NOT EXISTS leads (
  tenant_id         TEXT NOT NULL,
  lead_id           TEXT NOT NULL,
  brand_id          TEXT NOT NULL DEFAULT 'default',
  source            TEXT,
  medium            TEXT,
  channel           TEXT,
  campaign_id       TEXT,
  landing_url       TEXT,
  status            TEXT NOT NULL DEFAULT 'new',
  crm_destination   TEXT,
  crm_lead_id       TEXT,
  contact_json      TEXT,
  payload_json      TEXT,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  PRIMARY KEY (tenant_id, lead_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant_status
  ON leads(tenant_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_leads_tenant_brand
  ON leads(tenant_id, brand_id, created_at DESC);
"""
