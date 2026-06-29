from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle


class KnowledgeArticleRepository(Protocol):
    def list_articles(self, tenant_id: str, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        ...

    def get_article(self, tenant_id: str, slug: str) -> KnowledgeArticle | None:
        ...

    def save_article(self, tenant_id: str, payload: dict, *, slug: str | None = None) -> KnowledgeArticle:
        ...

    def delete_article(self, tenant_id: str, slug: str) -> dict:
        ...
