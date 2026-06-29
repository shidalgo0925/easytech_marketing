"""Composite repository — json | sql | dual."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.platform_infrastructure.db import publication_json_enabled, publication_sql_enabled
from Motor_Tecnico.accio_engine.publication_domain.model import Publication
from Motor_Tecnico.accio_engine.publication_domain.ports import PublicationRepository

from .json_repository import JsonPublicationRepository
from .sqlite_repository import SqlitePublicationRepository


class CompositePublicationRepository:
    def __init__(
        self,
        json_repo: PublicationRepository | None = None,
        sql_repo: PublicationRepository | None = None,
    ) -> None:
        self._json = json_repo or JsonPublicationRepository()
        self._sql = sql_repo or SqlitePublicationRepository()

    def load_queue(self, tenant_id: str, brand_id: str) -> dict:
        if publication_sql_enabled():
            data = self._sql.load_queue(tenant_id, brand_id)
            if data.get("posts"):
                return data
        if publication_json_enabled():
            return self._json.load_queue(tenant_id, brand_id)
        return {"posts": []}

    def save_queue(self, tenant_id: str, brand_id: str, data: dict) -> None:
        if publication_sql_enabled():
            self._sql.save_queue(tenant_id, brand_id, data)
        if publication_json_enabled():
            self._json.save_queue(tenant_id, brand_id, data)

    def list_publications(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        status: str | None = None,
    ) -> list[Publication]:
        if publication_sql_enabled():
            rows = self._sql.list_publications(tenant_id, brand_id, status=status)
            if rows:
                return rows
        if publication_json_enabled():
            return self._json.list_publications(tenant_id, brand_id, status=status)
        return []

    def get_publication(self, tenant_id: str, brand_id: str, publication_id: str) -> Publication | None:
        if publication_sql_enabled():
            row = self._sql.get_publication(tenant_id, brand_id, publication_id)
            if row is not None:
                return row
        if publication_json_enabled():
            return self._json.get_publication(tenant_id, brand_id, publication_id)
        return None
