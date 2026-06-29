from __future__ import annotations

from functools import wraps

from Motor_Tecnico.accio_engine.knowledge_article_api.composition import (
    knowledge_article_use_cases,
    reset_knowledge_article_use_cases,
    tenant_context,
)
from Motor_Tecnico.accio_engine.knowledge_article_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.legacy_mapper import article_to_legacy_detail


def reset_use_cases_cache() -> None:
    reset_knowledge_article_use_cases()


def _success(data, *, status: int = 200):
    from flask import jsonify

    return jsonify({"ok": True, "data": data}), status


def _error(exc: ApplicationError):
    from flask import jsonify

    return jsonify({"ok": False, "error": exc.code, "message": exc.message}), exc.http_status


def _article_response(article: KnowledgeArticle, *, detail: bool = False) -> dict:
    if detail:
        return article_to_legacy_detail(article)
    return article.to_api_dict(include_body=False)


def register_knowledge_article_api(app, auth_decorator) -> None:
    base = "/api/v1/tenants/<tenant_id>/knowledge/articles"

    def _handle(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            try:
                return view(*args, **kwargs)
            except ApplicationError as exc:
                return _error(exc)
            except PermissionError as exc:
                return _error(ApplicationError("forbidden", str(exc), 403))

        return wrapped

    @app.get(base)
    @auth_decorator
    @_handle
    def api_list_knowledge_articles(tenant_id: str):
        from flask import request

        brand_id = request.args.get("brand_id") or request.args.get("app_id")
        ctx = tenant_context(tenant_id)
        rows = knowledge_article_use_cases().list_articles(ctx, brand_id=brand_id)
        return _success([_article_response(a) for a in rows])

    @app.get(f"{base}/<slug>")
    @auth_decorator
    @_handle
    def api_get_knowledge_article(tenant_id: str, slug: str):
        ctx = tenant_context(tenant_id)
        row = knowledge_article_use_cases().get_article(ctx, slug)
        return _success(_article_response(row, detail=True))
