"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import knowledge_json_enabled, knowledge_sql_enabled
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_domain.ports import KnowledgeArticleRepository

from .json_repository import JsonKnowledgeArticleRepository
from .sqlite_repository import SqliteKnowledgeArticleRepository


class CompositeKnowledgeArticleRepository:
    def __init__(
        self,
        json_repo: KnowledgeArticleRepository | None = None,
        sql_repo: KnowledgeArticleRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonKnowledgeArticleRepository()
        self._sql = sql_repo or SqliteKnowledgeArticleRepository()

    def list_articles(self, tenant_id: str, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        if knowledge_sql_enabled():
            rows = self._sql.list_articles(tenant_id, brand_id=brand_id)
            if rows:
                return rows
        if knowledge_json_enabled():
            return self._json.list_articles(tenant_id, brand_id=brand_id)
        return []

    def get_article(self, tenant_id: str, slug: str) -> KnowledgeArticle | None:
        if knowledge_sql_enabled():
            row = self._sql.get_article(tenant_id, slug)
            if row is not None:
                return row
        if knowledge_json_enabled():
            return self._json.get_article(tenant_id, slug)
        return None

    def save_article(self, tenant_id: str, payload: dict, *, slug: str | None = None) -> KnowledgeArticle:
        article: KnowledgeArticle | None = None
        if knowledge_sql_enabled():
            article = self._sql.save_article(tenant_id, payload, slug=slug)
        if knowledge_json_enabled():
            article = self._json.save_article(tenant_id, payload, slug=slug)
        if article is None:
            raise RuntimeError("No knowledge store enabled")
        return article

    def delete_article(self, tenant_id: str, slug: str) -> dict:
        result: dict | None = None
        if knowledge_sql_enabled():
            result = self._sql.delete_article(tenant_id, slug)
        if knowledge_json_enabled():
            result = self._json.delete_article(tenant_id, slug)
        if result is None:
            raise RuntimeError("No knowledge store enabled")
        return result
