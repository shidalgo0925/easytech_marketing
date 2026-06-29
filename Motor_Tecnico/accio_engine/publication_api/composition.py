from __future__ import annotations

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.publication_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.publication_application.use_cases import GetPublication, ListPublications
from Motor_Tecnico.accio_engine.publication_domain.service import PublicationDomainService
from Motor_Tecnico.accio_engine.publication_infrastructure.application_adapters import PublicationRbacAdapter
from Motor_Tecnico.accio_engine.publication_infrastructure.composite_repository import CompositePublicationRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema


def build_publication_domain_service() -> PublicationDomainService:
    ensure_schema()
    return PublicationDomainService(CompositePublicationRepository())


class PublicationUseCases:
    def __init__(self) -> None:
        pubs = build_publication_domain_service()
        auth = PublicationRbacAdapter()
        self.list_publications = ListPublications(pubs, auth)
        self.get_publication = GetPublication(pubs, auth)


_USE_CASES: PublicationUseCases | None = None


def publication_use_cases() -> PublicationUseCases:
    global _USE_CASES
    if _USE_CASES is None:
        _USE_CASES = PublicationUseCases()
    return _USE_CASES


def reset_publication_use_cases() -> None:
    global _USE_CASES
    _USE_CASES = None


def tenant_app_context(tenant_id: str, app_id: str) -> TenantAppContext:
    return TenantAppContext(
        tenant_id=tenant_id,
        app_id=marketing_app.normalize_app_id(app_id),
    )
