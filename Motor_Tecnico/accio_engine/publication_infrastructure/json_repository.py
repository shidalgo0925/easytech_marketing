"""JSON adapter — content_queue.json per app."""

from __future__ import annotations

import json
from pathlib import Path

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.publication_domain.model import Publication
from Motor_Tecnico.accio_engine.publication_infrastructure.legacy_mapper import (
    post_to_publication,
    publication_to_post,
    queue_to_publications,
)


class JsonPublicationRepository:
    def _path(self, tenant_id: str, brand_id: str) -> Path:
        return marketing_app.queue_file_path(tenant_id, brand_id)

    def _read_raw(self, tenant_id: str, brand_id: str) -> dict:
        path = self._path(tenant_id, brand_id)
        if not path.is_file():
            return {"posts": []}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_queue(self, tenant_id: str, brand_id: str) -> dict:
        return self._read_raw(tenant_id, brand_id)

    def save_queue(self, tenant_id: str, brand_id: str, data: dict) -> None:
        path = self._path(tenant_id, brand_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def list_publications(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        status: str | None = None,
    ) -> list[Publication]:
        pubs = queue_to_publications(tenant_id, brand_id, self._read_raw(tenant_id, brand_id))
        if status:
            st = status.strip().lower()
            pubs = [p for p in pubs if p.status.lower() == st]
        return pubs

    def get_publication(self, tenant_id: str, brand_id: str, publication_id: str) -> Publication | None:
        for pub in self.list_publications(tenant_id, brand_id):
            if pub.publication_id == publication_id or pub.legacy_queue_id == publication_id:
                return pub
        return None
