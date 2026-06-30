"""Content Engine application use cases."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine.campaign_infrastructure.application_adapters import CampaignRbacAdapter
from Motor_Tecnico.accio_engine.content_engine_application.errors import ApplicationError, from_content_error
from Motor_Tecnico.accio_engine.content_engine_domain.engine_service import ContentEngineService
from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_infrastructure.engine_orchestrator import ContentEngineOrchestrator
from Motor_Tecnico.accio_engine.content_engine_infrastructure import memory_bridge as content_memory
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService


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


class ListContentPublishQueue:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, *, limit: int = 50) -> list[ContentPiece]:
        self._auth.require_permission(ctx, "read")
        return self._engine.list_publish_queue(ctx.tenant_id, limit=limit)


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
    def __init__(
        self,
        engine: ContentEngineService,
        auth: CampaignRbacAdapter,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._engine = engine
        self._auth = auth
        self._memory = memory

    def __call__(self, ctx: TenantContext, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            saved = self._engine.approve(ctx.tenant_id, content_id, actor_id=actor_id)
            content_memory.record_content_approved(self._memory, piece=saved, actor_id=actor_id)
            return saved
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class RejectContentPiece:
    def __init__(
        self,
        engine: ContentEngineService,
        auth: CampaignRbacAdapter,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._engine = engine
        self._auth = auth
        self._memory = memory

    def __call__(
        self,
        ctx: TenantContext,
        content_id: str,
        *,
        reason: str = "",
        actor_id: str = "system",
    ) -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            saved = self._engine.reject(
                ctx.tenant_id, content_id, reason=reason, actor_id=actor_id,
            )
            content_memory.record_content_rejected(
                self._memory, piece=saved, actor_id=actor_id, reason=reason,
            )
            return saved
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class QueueContentPiece:
    def __init__(
        self,
        engine: ContentEngineService,
        auth: CampaignRbacAdapter,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._engine = engine
        self._auth = auth
        self._memory = memory

    def __call__(self, ctx: TenantContext, content_id: str, *, actor_id: str = "system") -> ContentPiece:
        self._auth.require_permission(ctx, "write")
        try:
            saved = self._engine.queue_for_publish(ctx.tenant_id, content_id, actor_id=actor_id)
            content_memory.record_content_queued(
                self._memory,
                piece=saved,
                actor_id=actor_id,
                queue_post_id=saved.queue_post_id or saved.content_id,
            )
            return saved
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class PublishContentNow:
    def __init__(
        self,
        engine: ContentEngineService,
        auth: CampaignRbacAdapter,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._engine = engine
        self._auth = auth
        self._memory = memory

    def __call__(
        self,
        ctx: TenantContext,
        content_id: str,
        *,
        actor_id: str = "system",
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        self._auth.require_permission(ctx, "write")
        try:
            from Motor_Tecnico.accio_engine.content_engine_infrastructure.publish_config import PublishConfig

            use_dry = dry_run if dry_run is not None else PublishConfig.from_env().dry_run
            preview = self._engine.get(ctx.tenant_id, content_id)
            content_memory.record_content_publish_started(
                self._memory, piece=preview, actor_id=actor_id, dry_run=use_dry,
            )
            piece, result = self._engine.publish_now(
                ctx.tenant_id, content_id, actor_id=actor_id, dry_run=dry_run,
            )
            if result.get("ok"):
                content_memory.record_content_published(
                    self._memory, piece=piece, actor_id=actor_id, result=result,
                )
            else:
                content_memory.record_content_publish_failed(
                    self._memory,
                    piece=piece,
                    actor_id=actor_id,
                    error_message=result.get("error_message") or "Error",
                    result=result,
                )
            return {
                "content_id": piece.content_id,
                "status": piece.status,
                "channel": piece.channel,
                "published_at": piece.published_at,
                "external_post_id": result.get("external_post_id"),
                "external_url": result.get("external_url"),
                "dry_run": result.get("dry_run", False),
                "error_message": result.get("error_message"),
                "piece": piece.to_api_dict(),
            }
        except ContentEngineError as exc:
            raise from_content_error(exc) from exc


class GetContentHistory:
    def __init__(self, engine: ContentEngineService, auth: CampaignRbacAdapter) -> None:
        self._engine = engine
        self._auth = auth

    def __call__(self, ctx: TenantContext, content_id: str, *, limit: int = 50) -> list[dict]:
        self._auth.require_permission(ctx, "read")
        try:
            return self._engine.list_history(ctx.tenant_id, content_id, limit=limit)
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
