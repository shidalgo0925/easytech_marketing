"""Recommendations schema — M10.3."""

_RECOMMENDATIONS_DDL = """
CREATE TABLE IF NOT EXISTS recommendations (
  tenant_id               TEXT NOT NULL,
  recommendation_id       TEXT NOT NULL,
  company_id              TEXT NOT NULL,
  brand_id                TEXT NOT NULL,
  roadmap_id              TEXT,
  title                   TEXT NOT NULL,
  description             TEXT,
  action                  TEXT NOT NULL,
  reason                  TEXT NOT NULL,
  expected_roi            TEXT,
  priority                TEXT NOT NULL,
  priority_score          REAL,
  owner_role              TEXT NOT NULL,
  owner_id                TEXT,
  due_at                  TEXT,
  status                  TEXT NOT NULL DEFAULT 'pending_approval',
  source                  TEXT NOT NULL,
  confidence              REAL NOT NULL DEFAULT 1.0,
  justification_refs_json TEXT,
  dependencies_json       TEXT,
  created_by              TEXT NOT NULL,
  approved_by             TEXT,
  rejected_by             TEXT,
  executed_at             TEXT,
  result_json             TEXT,
  created_at              TEXT NOT NULL,
  updated_at              TEXT NOT NULL,
  PRIMARY KEY (tenant_id, recommendation_id)
);

CREATE INDEX IF NOT EXISTS idx_recommendations_inbox
  ON recommendations(tenant_id, owner_role, status, priority_score DESC);

CREATE INDEX IF NOT EXISTS idx_recommendations_roadmap
  ON recommendations(tenant_id, roadmap_id);

CREATE INDEX IF NOT EXISTS idx_recommendations_brand
  ON recommendations(tenant_id, brand_id, status, created_at DESC);
"""
