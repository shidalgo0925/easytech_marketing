"""Content Engine application use cases."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.campaign_infrastructure.application_adapters import CampaignRbacAdapter
from Motor_Tecnico.accio_engine.content_engine_application.errors import ApplicationError, from_content_error
from Motor_Tecnico.accio_engine.content_engine_domain.engine_service import ContentEngineService
from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_infrastructure.engine_orchestrator import ContentEngineOrchestrator
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext


class ListContentPieces:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(
        self,
        ctx: TenantContext,
        *,
        status: str | None = None,
        campaign_id: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[ContentPiece]:
        self._auth.require_permission(ctx, "read")
        return self._engine.list_content(
            ctx.tenant_id,
            status=status,
            campaign_id=campaign_id,
            brand_id=brand_id,
            limit=limit,
        )


class GetContentPiece:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str) -> ContentPiece:
        self._auth.require_permission(ctx, "read")
        try:
            return self._engine.get(ctx.tenant_id, content_id)
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class CreateContentFromCampaign:
    def __init__(self, orchestrator: ContentEngineOrchestrator, auth: CampaignRbacAdapter) -> None:
        self._orchestrator = orchestrator
        self._auth = auth

    def __call__(
        self,
        ctx: TenantContext,
        campaign_id: str,
        *,
        enrich: bool = False,
        actor_id: str = "system",
    ) -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            return self._orchestrator.from_campaign(
                ctx.tenant_id,
                campaign_id,
                actor_id=actor_id,
                enrich=enrich,
            )
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class EnrichContentPiece:
    def __init__(self, orchestrator: ContentEngineOrchestrator, auth: CampaignRbacAdapter) -> None:
        self._orchestrator = orchestrator
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            return self._orchestrator.enrich_content(ctx.tenant_id, content_id, actor_id=actor_id)
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class PatchContentPiece:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str, fields: dict[str, Any]) -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            return self._engine.update_fields(ctx.tenant_id, content_id, **fields)
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class ApproveContentPiece:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            return self._engine.approve(ctx.tenant_id, content_id, actor_id=actor_id)
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class GetContentExplain:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str) -> dict:
        self._auth.require_permission(ctx, "read")
        try:
            piece = self._engine.get(ctx.tenant_id, content_id)
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc
        if not piece.explain:
            raise ApplicationError("explain_not_found", "No hay explicación para este contenido", 404)
        return {
            "content_id": content_id,
            "explain": piece.explain,
            "llm_enrichment": piece.llm_enrichment,
            "llm_skipped": piece.llm_skipped,
        }
