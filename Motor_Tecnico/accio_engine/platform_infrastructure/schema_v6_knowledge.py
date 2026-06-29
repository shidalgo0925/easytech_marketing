"""Knowledge articles schema — M6."""

_KNOWLEDGE_ARTICLES_DDL = """
CREATE TABLE IF NOT EXISTS knowledge_articles (
  tenant_id       TEXT NOT NULL,
  article_id      TEXT NOT NULL,
  slug            TEXT NOT NULL,
  title           TEXT NOT NULL,
  product_ref     TEXT,
  brand_id        TEXT,
  legacy_file     TEXT,
  content_md      TEXT NOT NULL,
  tags_json       TEXT,
  status          TEXT NOT NULL DEFAULT 'published',
  published_at    TEXT,
  payload_json    TEXT,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  PRIMARY KEY (tenant_id, article_id),
  UNIQUE (tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_tenant_brand
  ON knowledge_articles(tenant_id, brand_id, status);
"""
