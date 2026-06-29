"""Facade for knowledge_api and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import knowledge_sql_enabled
from Motor_Tecnico.accio_engine.knowledge_article_domain.errors import KnowledgeArticleNotFound
from Motor_Tecnico.accio_engine.knowledge_article_domain.service import KnowledgeArticleDomainService
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.composite_repository import (
    CompositeKnowledgeArticleRepository,
)
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.legacy_mapper import (
    article_to_legacy_detail,
    article_to_legacy_list_item,
)

_SERVICE: KnowledgeArticleDomainService | None = None


def get_knowledge_article_service() -> KnowledgeArticleDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = KnowledgeArticleDomainService(CompositeKnowledgeArticleRepository())
    return _SERVICE


def reset_knowledge_article_service() -> None:
    global _SERVICE
    _SERVICE = None


def knowledge_store_active() -> bool:
    return knowledge_sql_enabled()


def list_knowledge(tenant_id: str) -> list[dict]:
    articles = get_knowledge_article_service().list_articles(tenant_id)
    return [article_to_legacy_list_item(a) for a in articles]


def load_article(slug: str, tenant_id: str) -> dict:
    try:
        article = get_knowledge_article_service().get_article(tenant_id, slug)
    except KnowledgeArticleNotFound as exc:
        raise FileNotFoundError(exc.message) from exc
    return article_to_legacy_detail(article)


def save_article(tenant_id: str, payload: dict, *, slug: str | None = None) -> dict:
    article = get_knowledge_article_service().save_article(tenant_id, payload, slug=slug)
    return article_to_legacy_detail(article)


def delete_article(slug: str, tenant_id: str) -> dict:
    try:
        return get_knowledge_article_service().delete_article(tenant_id, slug)
    except KnowledgeArticleNotFound as exc:
        raise FileNotFoundError(exc.message) from exc
