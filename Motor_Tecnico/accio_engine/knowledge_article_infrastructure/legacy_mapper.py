"""Legacy knowledge manifest + *.md ↔ KnowledgeArticle."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_md_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_intro"
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip().lower()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections


def product_to_brand_id(tenant_id: str, product_ref: str) -> str:
    if tenant_id == DEFAULT_TENANT:
        mapped = marketing_app._PRODUCT_SLUG_TO_APP.get(product_ref)
        if mapped:
            return mapped
        mapped = marketing_app._PRODUCT_SLUG_TO_APP.get(product_ref.replace("-", "_"))
        if mapped:
            return mapped
    return marketing_app.DEFAULT_APP_ID


def manifest_entry_to_article(tenant_id: str, entry: dict[str, Any], body: str = "") -> KnowledgeArticle:
    slug = (entry.get("slug") or "").strip().lower()
    product_ref = (entry.get("product") or slug).strip()
    tags = entry.get("tags") or []
    now = _utc_now()
    return KnowledgeArticle(
        tenant_id=tenant_id,
        article_id=slug,
        slug=slug,
        title=(entry.get("title") or slug).strip(),
        content_md=body,
        product_ref=product_ref,
        brand_id=product_to_brand_id(tenant_id, product_ref),
        legacy_file=entry.get("file") or f"{slug}.md",
        tags=list(tags),
        status=entry.get("status", "published"),
        published_at=entry.get("published_at") or now,
        payload={},
        created_at=now,
        updated_at=now,
    )


def payload_to_article(tenant_id: str, payload: dict[str, Any], *, slug: str | None = None) -> KnowledgeArticle:
    raw_slug = (slug or payload.get("slug") or "").strip().lower()
    body = payload.get("body") or ""
    tags = payload.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    entry = {
        "slug": raw_slug,
        "title": (payload.get("title") or raw_slug).strip(),
        "product": (payload.get("product") or raw_slug).strip(),
        "tags": tags,
        "file": f"{raw_slug}.md",
        "status": payload.get("status", "published"),
    }
    return manifest_entry_to_article(tenant_id, entry, body)


def article_to_row(article: KnowledgeArticle) -> dict[str, Any]:
    return {
        "tenant_id": article.tenant_id,
        "article_id": article.article_id,
        "slug": article.slug,
        "title": article.title,
        "product_ref": article.product_ref,
        "brand_id": article.brand_id,
        "legacy_file": article.legacy_file,
        "content_md": article.content_md,
        "tags_json": json.dumps(article.tags or [], ensure_ascii=False),
        "status": article.status,
        "published_at": article.published_at,
        "payload_json": json.dumps(article.payload or {}, ensure_ascii=False),
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


def row_to_article(row: Any) -> KnowledgeArticle:
    return KnowledgeArticle(
        tenant_id=row["tenant_id"],
        article_id=row["article_id"],
        slug=row["slug"],
        title=row["title"],
        content_md=row["content_md"] or "",
        product_ref=row["product_ref"] or "",
        brand_id=row["brand_id"] or marketing_app.DEFAULT_APP_ID,
        legacy_file=row["legacy_file"] or "",
        tags=json.loads(row["tags_json"] or "[]"),
        status=row["status"],
        published_at=row["published_at"] or "",
        payload=json.loads(row["payload_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def article_to_legacy_list_item(article: KnowledgeArticle) -> dict[str, Any]:
    return article.to_api_dict(include_body=False)


def article_to_legacy_detail(article: KnowledgeArticle) -> dict[str, Any]:
    row = article.to_api_dict(include_body=True)
    row["sections"] = parse_md_sections(article.content_md)
    return row
