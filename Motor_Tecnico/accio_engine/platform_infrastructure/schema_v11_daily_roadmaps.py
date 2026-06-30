"""Daily roadmaps schema — M10.4."""

_DAILY_ROADMAPS_DDL = """
CREATE TABLE IF NOT EXISTS daily_roadmaps (
  tenant_id           TEXT NOT NULL,
  roadmap_id          TEXT NOT NULL,
  company_id          TEXT NOT NULL,
  roadmap_date        TEXT NOT NULL,
  generated_at        TEXT NOT NULL,
  generator_version   TEXT NOT NULL DEFAULT 'decision_engine_v1',
  summary_json        TEXT,
  PRIMARY KEY (tenant_id, roadmap_id),
  UNIQUE (tenant_id, company_id, roadmap_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_roadmaps_date
  ON daily_roadmaps(tenant_id, roadmap_date DESC);
"""
