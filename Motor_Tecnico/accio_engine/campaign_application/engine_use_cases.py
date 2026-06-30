"""Campaign Engine — application use cases."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from Motor_Tecnico.accio_engine.campaign_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.campaign_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.campaign_domain.campaign_explainability import explain_from_campaign
from Motor_Tecnico.accio_engine.campaign_domain.engine_service import CampaignEngineService
from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_infrastructure.engine_orchestrator import CampaignEngineOrchestrator
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext


class ListEngineCampaigns:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        status: str | None = None,
        brand_id: str | None = None,
        limit: int = 50,
    ) -> list[Campaign]:
        self._authorization.require_permission(ctx, "read")
        return self._engine.list_campaigns(ctx.tenant_id, status=status, brand_id=brand_id, limit=limit)


class GetEngineCampaign:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str) -> Campaign:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._engine.get(ctx.tenant_id, campaign_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class CreateCampaignFromRecommendation:
    def __init__(self, orchestrator: CampaignEngineOrchestrator, authorization: AuthorizationPort) -> None:
        self._orchestrator = orchestrator
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        recommendation_id: str,
        *,
        actor_id: str = "system",
        enrich: bool = False,
    ) -> Campaign:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._orchestrator.from_recommendation(
                ctx.tenant_id,
                recommendation_id,
                actor_id=actor_id,
                enrich=enrich,
            )
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class EnrichCampaign:
    def __init__(self, orchestrator: CampaignEngineOrchestrator, authorization: AuthorizationPort) -> None:
        self._orchestrator = orchestrator
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str, *, actor_id: str = "system") -> Campaign:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._orchestrator.enrich_campaign(ctx.tenant_id, campaign_id, actor_id=actor_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class PatchCampaign:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str, fields: dict[str, Any]) -> Campaign:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._engine.update_fields(ctx.tenant_id, campaign_id, **fields)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class ApproveCampaign:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str, *, actor_id: str = "system") -> Campaign:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._engine.approve(ctx.tenant_id, campaign_id, actor_id=actor_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class ArchiveCampaign:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str, *, actor_id: str = "system") -> Campaign:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._engine.archive(ctx.tenant_id, campaign_id, actor_id=actor_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc


class GetCampaignExplain:
    def __init__(self, engine: CampaignEngineService, authorization: AuthorizationPort) -> None:
        self._engine = engine
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, campaign_id: str) -> dict:
        self._authorization.require_permission(ctx, "read")
        try:
            campaign = self._engine.get(ctx.tenant_id, campaign_id)
        except CampaignError as exc:
            raise ApplicationError.from_domain(exc) from exc
        explain = explain_from_campaign(campaign)
        if not explain:
            raise ApplicationError("explain_not_found", "No hay explicación para esta campaña", 404)
        return {
            "campaign_id": campaign_id,
            "explain": explain,
            "llm_enrichment": campaign.llm_enrichment,
            "llm_skipped": campaign.llm_skipped,
        }
