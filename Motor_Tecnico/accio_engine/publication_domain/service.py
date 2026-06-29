from __future__ import annotations

from Motor_Tecnico.accio_engine.publication_domain.errors import PublicationNotFound
from Motor_Tecnico.accio_engine.publication_domain.model import Publication
from Motor_Tecnico.accio_engine.publication_domain.ports import PublicationRepository


class PublicationDomainService:
    def __init__(self, repository: PublicationRepository) -> None:
        self._repo = repository

    def load_queue(self, tenant_id: str, brand_id: str) -> dict:
        return self._repo.load_queue(tenant_id, brand_id)

    def save_queue(self, tenant_id: str, brand_id: str, data: dict) -> None:
        self._repo.save_queue(tenant_id, brand_id, data)

    def list_publications(
        self,
        tenant_id: str,
        brand_id: str,
        *,
        status: str | None = None,
    ) -> list[Publication]:
        return self._repo.list_publications(tenant_id, brand_id, status=status)

    def get_publication(self, tenant_id: str, brand_id: str, publication_id: str) -> Publication:
        row = self._repo.get_publication(tenant_id, brand_id, publication_id)
        if row is None:
            raise PublicationNotFound(f"Publicación no encontrada: {publication_id}")
        return row
