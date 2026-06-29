"""JSON adapter — knowledge/manifest.json + *.md."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from Motor_Tecnico.accio_engine.knowledge_article_domain.model import KnowledgeArticle
from Motor_Tecnico.accio_engine.knowledge_article_infrastructure.legacy_mapper import (
    article_to_legacy_list_item,
    manifest_entry_to_article,
    payload_to_article,
)
from Motor_Tecnico.accio_engine.tenant import effective_paths, resolve_tenant


class JsonKnowledgeArticleRepository:
    def _paths(self, tenant_id: str) -> dict[str, Path]:
        return effective_paths(resolve_tenant(tenant_id))

    def _read_manifest(self, tenant_id: str) -> dict[str, Any]:
        path = self._paths(tenant_id)["knowledge_manifest"]
        if not path.is_file():
            return {"articles": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_manifest(self, tenant_id: str, manifest: dict[str, Any]) -> None:
        path = self._paths(tenant_id)["knowledge_manifest"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def list_articles(self, tenant_id: str, *, brand_id: str | None = None) -> list[KnowledgeArticle]:
        paths = self._paths(tenant_id)
        manifest = self._read_manifest(tenant_id)
        rows: list[KnowledgeArticle] = []
        for entry in manifest.get("articles", []):
            article = manifest_entry_to_article(tenant_id, entry)
            path = paths["knowledge_dir"] / entry.get("file", f"{article.slug}.md")
            if path.is_file():
                article = manifest_entry_to_article(tenant_id, entry, path.read_text(encoding="utf-8"))
            if brand_id and article.brand_id != brand_id:
                continue
            rows.append(article)
        return rows

    def get_article(self, tenant_id: str, slug: str) -> KnowledgeArticle | None:
        paths = self._paths(tenant_id)
        manifest = self._read_manifest(tenant_id)
        entry = next((a for a in manifest.get("articles", []) if a.get("slug") == slug), None)
        if not entry:
            return None
        path = paths["knowledge_dir"] / entry.get("file", f"{slug}.md")
        body = path.read_text(encoding="utf-8") if path.is_file() else ""
        return manifest_entry_to_article(tenant_id, entry, body)

    def save_article(self, tenant_id: str, payload: dict[str, Any], *, slug: str | None = None) -> KnowledgeArticle:
        paths = self._paths(tenant_id)
        manifest = self._read_manifest(tenant_id)
        articles: list[dict[str, Any]] = list(manifest.get("articles") or [])
        article = payload_to_article(tenant_id, payload, slug=slug)
        raw_slug = article.slug
        if not raw_slug or not raw_slug.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Slug de artículo inválido")
        paths["knowledge_dir"].mkdir(parents=True, exist_ok=True)
        (paths["knowledge_dir"] / article.legacy_file).write_text(article.content_md, encoding="utf-8")
        entry = {
            "slug": article.slug,
            "title": article.title,
            "product": article.product_ref,
            "tags": article.tags,
            "file": article.legacy_file,
        }
        found = False
        for i, row in enumerate(articles):
            if row.get("slug") == raw_slug:
                articles[i] = {**row, **entry}
                found = True
                break
        if not found:
            articles.append(entry)
        manifest["articles"] = articles
        manifest["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._write_manifest(tenant_id, manifest)
        return article

    def delete_article(self, tenant_id: str, slug: str) -> dict:
        paths = self._paths(tenant_id)
        manifest = self._read_manifest(tenant_id)
        articles = list(manifest.get("articles") or [])
        entry = next((a for a in articles if a.get("slug") == slug), None)
        if not entry:
            raise FileNotFoundError(f"Artículo no encontrado: {slug}")
        articles = [a for a in articles if a.get("slug") != slug]
        manifest["articles"] = articles
        manifest["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._write_manifest(tenant_id, manifest)
        file_path = paths["knowledge_dir"] / entry.get("file", f"{slug}.md")
        if file_path.is_file():
            file_path.unlink()
        return {"slug": slug, "deleted": True}

    def list_legacy(self, tenant_id: str) -> list[dict[str, Any]]:
        return [article_to_legacy_list_item(a) for a in self.list_articles(tenant_id)]
