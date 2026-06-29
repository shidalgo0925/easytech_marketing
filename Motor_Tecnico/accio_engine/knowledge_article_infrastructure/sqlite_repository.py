"""SQLite adapter — knowledge_articles table."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import datetime, timezone

from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.legacy_mapper import (
    article_to_row,
    payload_to_article,
    row_to_article,
)


class SqliteKnowledgeArticleRepository:
    def __init__(self, connection: sqlite3.Connection | None = None) -> None:
        self._external = connection
        if connection is not None:
            ensure_schema(connection)

    def _conn(self) -> sqlite3.Connection:
        if self._external is not None:
            return self._external
        conn = get_connection()
        ensure_schema(conn)
        return conn

    def list_articles(self, tenant_id: str, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        conn = self._conn()
        try:
            sql = "SELECT * FROM knowledge_articles WHERE tenant_id = ?"
            params: list[str] = [tenant_id]
            if brand_id:
                sql += " AND brand_id = ?"
                params.append(brand_id)
            sql += " ORDER BY title COLLATE NOCASE"
            rows = conn.execute(sql, params).fetchall()
            return [row_to_article(r) for r in rows]
        finally:
            if self._external is None:
                conn.close()

    def get_article(self, tenant_id: str, slug: str) -> KnowledgeArticle | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM knowledge_articles WHERE tenant_id = ? AND slug = ?",
                (tenant_id, slug),
            ).fetchone()
            return row_to_article(row) if row else None
        finally:
            if self._external is None:
                conn.close()

    def save_article(self, tenant_id: str, payload: dict, *, slug: str | None = None) -> KnowledgeArticle:
        article = payload_to_article(tenant_id, payload, slug=slug)
        now = datetime.now(timezone.utc).isoformat()
        article = KnowledgeArticle(
            tenant_id=article.tenant_id,
            article_id=article.article_id,
            slug=article.slug,
            title=article.title,
            content_md=article.content_md,
            product_ref=article.product_ref,
            brand_id=article.brand_id,
            legacy_file=article.legacy_file,
            tags=article.tags,
            status=article.status,
            published_at=article.published_at or now,
            payload=article.payload,
            created_at=now,
            updated_at=now,
        )
        conn = self._conn()
        try:
            existing = conn.execute(
                "SELECT created_at FROM knowledge_articles WHERE tenant_id = ? AND slug = ?",
                (tenant_id, article.slug),
            ).fetchone()
            if existing:
                article = replace(article, created_at=existing["created_at"], updated_at=now)
            conn.execute(
                """
                INSERT INTO knowledge_articles (
                  tenant_id, article_id, slug, title, product_ref, brand_id,
                  legacy_file, content_md, tags_json, status, published_at,
                  payload_json, created_at, updated_at
                ) VALUES (
                  :tenant_id, :article_id, :slug, :title, :product_ref, :brand_id,
                  :legacy_file, :content_md, :tags_json, :status, :published_at,
                  :payload_json, :created_at, :updated_at
                )
                ON CONFLICT(tenant_id, article_id) DO UPDATE SET
                  slug = excluded.slug,
                  title = excluded.title,
                  product_ref = excluded.product_ref,
                  brand_id = excluded.brand_id,
                  legacy_file = excluded.legacy_file,
                  content_md = excluded.content_md,
                  tags_json = excluded.tags_json,
                  status = excluded.status,
                  published_at = excluded.published_at,
                  payload_json = excluded.payload_json,
                  updated_at = excluded.updated_at
                """,
                article_to_row(article),
            )
            conn.commit()
            return article
        finally:
            if self._external is None:
                conn.close()

    def delete_article(self, tenant_id: str, slug: str) -> dict:
        conn = self._conn()
        try:
            conn.execute(
                "DELETE FROM knowledge_articles WHERE tenant_id = ? AND slug = ?",
                (tenant_id, slug),
            )
            conn.commit()
            return {"slug": slug, "deleted": True}
        finally:
            if self._external is None:
                conn.close()

    def save_all_for_tenant(self, tenant_id: str, articles: list[KnowledgeArticle]) -> None:
        conn = self._conn()
        try:
            conn.execute("DELETE FROM knowledge_articles WHERE tenant_id = ?", (tenant_id,))
            for article in articles:
                conn.execute(
                    """
                    INSERT INTO knowledge_articles (
                      tenant_id, article_id, slug, title, product_ref, brand_id,
                      legacy_file, content_md, tags_json, status, published_at,
                      payload_json, created_at, updated_at
                    ) VALUES (
                      :tenant_id, :article_id, :slug, :title, :product_ref, :brand_id,
                      :legacy_file, :content_md, :tags_json, :status, :published_at,
                      :payload_json, :created_at, :updated_at
                    )
                    """,
                    article_to_row(article),
                )
            conn.commit()
        finally:
            if self._external is None:
                conn.close()
