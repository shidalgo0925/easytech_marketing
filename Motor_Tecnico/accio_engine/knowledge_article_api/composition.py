from __future__ import annotations

from Motor_Tecnico.accio_engine.knowledge_article_application.context import TenantContext
from Motor_Tecnico.accio_engine.knowledge_article_application.use_cases import GetKnowledgeArticle, ListKnowledgeArticles
from Motor_Tecnico.accio_engine.knowledge_article_domain.service import KnowledgeArticleDomainService
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.application_adapters import KnowledgeArticleRbacAdapter
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.composite_repository import (
    CompositeKnowledgeArticleRepository,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_knowledge_article_domain_service() -> KnowledgeArticleDomainService:
    ensure_schema()
    return KnowledgeArticleDomainService(CompositeKnowledgeArticleRepository())


class KnowledgeArticleUseCases:
    def __init__(self) -> None:
        articles = build_knowledge_article_domain_service()
        auth = KnowledgeArticleRbacAdapter()
        self.list_articles = ListKnowledgeArticles(articles, auth)
        self.get_article = GetKnowledgeArticle(articles, auth)


_USE_CASES: KnowledgeArticleUseCases | None = None


def knowledge_article_use_cases() -> KnowledgeArticleUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = KnowledgeArticleUseCases()
    return _USE_CASES


def reset_knowledge_article_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_context(tenant_id: str) -> TenantContext:
    return TenantContext(tenant_id=tenant_id)
