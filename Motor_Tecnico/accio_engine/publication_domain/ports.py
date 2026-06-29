from __future__ import annotations

from typing import Protocol

from Motor_Tecnico.accio_engine.publication_domain.model import Publication


class PublicationRepository(Protocol):
    def load_queue(self, tenant_id: str, brand_id: str) -> dict:
        ...

    def save_queue(self, tenant_id: str, brand_id: str, data: dict) -> None:
        ...

    def list_publications(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        status: str | None = None,
    ) -> list[Publication]:
        ...

    def get_publication(self, tenant_id: str, brand_id: str, publication_id: str) -> Publication | None:
        ...
