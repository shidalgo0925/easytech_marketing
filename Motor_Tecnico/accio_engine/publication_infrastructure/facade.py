"""Facade for executor and API."""

from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.platform_infrastructure.db import publication_sql_enabled
from Motor_Tecnico.accio_engine.publication_domain.service import PublicationDomainService
from Motor_Tecnico.accio_engine.publication_infrastructure.composite_repository import CompositePublicationRepository

_SERVICE: PublicationDomainService | None = None


def get_publication_service() -> PublicationDomainService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = PublicationDomainService(CompositePublicationRepository())
    return _SERVICE


def reset_publication_service() -> None:
    global _SERVICE
    _SERVICE = None


def _resolve_brand_id(tenant_id: str, app_id: str | None) -> str:
    return marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))


def publication_store_active() -> bool:
    return publication_sql_enabled()


def load_content_queue(tenant_id: str, app_id: str | None = None) -> dict:
    brand_id = _resolve_brand_id(tenant_id, app_id)
    return get_publication_service().load_queue(tenant_id, brand_id)


def save_content_queue(data: dict, tenant_id: str, app_id: str | None = None) -> None:
    brand_id = _resolve_brand_id(tenant_id, app_id)
    get_publication_service().save_queue(tenant_id, brand_id, data)
