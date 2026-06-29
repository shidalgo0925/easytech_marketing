"""Company Brain schema — M2."""

_COMPANY_PROFILES_DDL = """
CREATE TABLE IF NOT EXISTS company_profiles (
  tenant_id         TEXT PRIMARY KEY,
  company_id        TEXT NOT NULL,
  profile_json      TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'published',
  valid_from        TEXT,
  source            TEXT,
  last_synced_at    TEXT,
  updated_at        TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_company_profiles_company
  ON company_profiles(company_id);
"""
