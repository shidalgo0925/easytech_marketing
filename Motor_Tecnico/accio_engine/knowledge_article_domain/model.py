from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class KnowledgeArticle:
    tenant_id: str
    article_id: str
    slug: str
    title: str
    content_md: str
    product_ref: str = ""
    brand_id: str = "default"
    legacy_file: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "published"
    published_at: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def to_api_dict(self, *, include_body: bool = False) -> dict[str, Any]:
        row = {
            "article_id": self.article_id,
            "slug": self.slug,
            "tenant_id": self.tenant_id,
            "title": self.title,
            "product": self.product_ref,
            "product_ref": self.product_ref,
            "brand_id": self.brand_id,
            "file": self.legacy_file or f"{self.slug}.md",
            "tags": self.tags,
            "status": self.status,
            "published_at": self.published_at,
            "available": bool(self.content_md),
            "chars": len(self.content_md or ""),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_body:
            row["body"] = self.content_md
        return row
