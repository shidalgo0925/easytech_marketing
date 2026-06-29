from __future__ import annotations

from Motor_Tecnico.accio_engine.knowledge_article_domain.errors import KnowledgeArticleNotFound
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_domain.ports import KnowledgeArticleRepository


class KnowledgeArticleDomainService:
    def __init__(self, repository: KnowledgeArticleRepository) -> None:
        self._repo = repository

    def list_articles(self, tenant_id: str, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        return self._repo.list_articles(tenant_id, brand_id=brand_id)

    def get_article(self, tenant_id: str, slug: str) -> KnowledgeArticle:
        row = self._repo.get_article(tenant_id, slug)
        if row is None:
            raise KnowledgeArticleNotFound(f"Artículo no encontrado: {slug}")
        return row

    def save_article(self, tenant_id: str, payload: dict, *, slug: str | None = None) -> KnowledgeArticle:
        return self._repo.save_article(tenant_id, payload, slug=slug)

    def delete_article(self, tenant_id: str, slug: str) -> dict:
        if self._repo.get_article(tenant_id, slug) is None:
            raise KnowledgeArticleNotFound(f"Artículo no encontrado: {slug}")
        return self._repo.delete_article(tenant_id, slug)
