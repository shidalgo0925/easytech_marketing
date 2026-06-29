from __future__ import annotations

from Motor_Tecnico.accio_engine.publication_application.context import TenantAppContext
from Motor_Tecnico.accio_engine.publication_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.publication_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.publication_domain.errors import PublicationError
from Motor_Tecnico.accio_engine.publication_domain.model import Publication
from Motor_Tecnico.accio_engine.publication_domain.service import PublicationDomainService


class ListPublications:
    def __init__(self, publications: PublicationDomainService, authorization: AuthorizationPort) -> None:
        self._publications = publications
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext, *, status: str | None = None) -> list[Publication]:
        self._authorization.require_permission(ctx, "read")
        return self._publications.list_publications(ctx.tenant_id, ctx.app_id, status=status)


class GetPublication:
    def __init__(self, publications: PublicationDomainService, authorization: AuthorizationPort) -> None:
        self._publications = publications
        self._authorization = authorization

    def __call__(self, ctx: TenantAppContext, publication_id: str) -> Publication:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._publications.get_publication(ctx.tenant_id, ctx.app_id, publication_id)
        except PublicationError as exc:
            raise ApplicationError.from_domain(exc) from exc
