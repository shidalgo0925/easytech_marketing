from __future__ import annotations

from Motor_Tecnico.accio_engine.knowledge_article_application.context import TenantContext
from Motor_Tecnico.accio_engine.knowledge_article_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.knowledge_article_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.knowledge_article_domain.errors import KnowledgeArticleError
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_domain.service import KnowledgeArticleDomainService


class ListKnowledgeArticles:
    def __init__(self, articles: KnowledgeArticleDomainService, authorization: AuthorizationPort) -> None:
        self._articles = articles
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        self._authorization.require_permission(ctx, "read")
        return self._articles.list_articles(ctx.tenant_id, brand_id=brand_id)


class GetKnowledgeArticle:
    def __init__(self, articles: KnowledgeArticleDomainService, authorization: AuthorizationPort) -> None:
        self._articles = articles
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, slug: str) -> KnowledgeArticle:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._articles.get_article(ctx.tenant_id, slug)
        except KnowledgeArticleError as exc:
            raise ApplicationError.from_domain(exc) from exc
