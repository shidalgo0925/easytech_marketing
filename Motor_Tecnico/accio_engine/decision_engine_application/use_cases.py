from __future__ import annotations

from datetime import datetime

from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapBundle, DailyRoadmapDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.errors import DecisionEngineError
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation, RecommendationCandidate
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.service import RoadmapBuilderService
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.memory_bridge import (
    record_daily_roadmap_generated,
    record_recommendation_accepted,
    record_recommendation_created,
    record_recommendation_rejected,
)
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled


class BuildRecommendationCandidates:
    """M10.1–M10.2 — evaluate rules, score, and return ordered draft candidates."""

    def __init__(self, builder: RoadmapBuilderService) -> None:
        self._builder = builder

    def __call__(
        self,
        ctx: TenantContext,
        *,
        reference_at: datetime | None = None,
    ) -> list[RecommendationCandidate]:
        return self._builder.build_candidates(ctx.tenant_id, reference_at=reference_at)


class CreateRecommendationFromCandidate:
    """M10.3 — persist candidate and emit RecommendationCreated."""

    def __init__(
        self,
        recommendations: RecommendationDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._recommendations = recommendations
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(
        self,
        ctx: TenantContext,
        candidate: RecommendationCandidate,
        *,
        created_by: str = "system",
    ) -> Recommendation:
        self._authorization.require_permission(ctx, "write")
        recommendation = self._recommendations.create_from_candidate(
            ctx.tenant_id,
            candidate,
            created_by=created_by,
        )
        record_recommendation_created(self._memory, recommendation=recommendation, actor_id=created_by)
        return recommendation


class ListRecommendations:
    def __init__(self, recommendations: RecommendationDomainService, authorization: AuthorizationPort) -> None:
        self._recommendations = recommendations
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        owner_role: str | None = None,
        limit: int = 50,
    ) -> list[Recommendation]:
        self._authorization.require_permission(ctx, "read")
        return self._recommendations.list_recommendations(
            ctx.tenant_id,
            brand_id=brand_id,
            status=status,
            owner_role=owner_role,
            limit=limit,
        )


class GetRecommendation:
    def __init__(self, recommendations: RecommendationDomainService, authorization: AuthorizationPort) -> None:
        self._recommendations = recommendations
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, recommendation_id: str) -> Recommendation:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._recommendations.get_recommendation(ctx.tenant_id, recommendation_id)
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc


class GenerateDailyRoadmap:
    """M10.4 — idempotent generate for a calendar date."""

    def __init__(
        self,
        roadmaps: DailyRoadmapDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._roadmaps = roadmaps
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, roadmap_date: str, *, created_by: str = "system") -> DailyRoadmapBundle:
        self._authorization.require_permission(ctx, "write")
        bundle = self._roadmaps.generate_daily_roadmap(
            ctx.tenant_id,
            roadmap_date,
            created_by=created_by,
        )
        if bundle.created:
            for recommendation in bundle.recommendations:
                record_recommendation_created(self._memory, recommendation=recommendation, actor_id=created_by)
            record_daily_roadmap_generated(
                self._memory,
                roadmap=bundle.roadmap,
                recommendation_count=len(bundle.recommendations),
                actor_id=created_by,
            )
        return bundle


class GetDailyRoadmap:
    def __init__(self, roadmaps: DailyRoadmapDomainService, authorization: AuthorizationPort) -> None:
        self._roadmaps = roadmaps
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, roadmap_date: str) -> DailyRoadmapBundle:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._roadmaps.get_daily_roadmap(ctx.tenant_id, roadmap_date)
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc


class ApproveRecommendation:
    """M10.5 — pending_approval|snoozed → approved."""

    def __init__(
        self,
        recommendations: RecommendationDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._recommendations = recommendations
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, recommendation_id: str, *, actor_id: str) -> Recommendation:
        self._authorization.require_permission(ctx, "write")
        try:
            row = self._recommendations.approve_recommendation(
                ctx.tenant_id,
                recommendation_id,
                actor_id=actor_id,
            )
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        record_recommendation_accepted(self._memory, recommendation=row, actor_id=actor_id)
        return row


class RejectRecommendation:
    """M10.5 — reject with mandatory reason."""

    def __init__(
        self,
        recommendations: RecommendationDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._recommendations = recommendations
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(
        self,
        ctx: TenantContext,
        recommendation_id: str,
        *,
        actor_id: str,
        reason: str,
    ) -> Recommendation:
        self._authorization.require_permission(ctx, "write")
        try:
            row = self._recommendations.reject_recommendation(
                ctx.tenant_id,
                recommendation_id,
                actor_id=actor_id,
                reason=reason,
            )
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        record_recommendation_rejected(self._memory, recommendation=row, actor_id=actor_id, reason=reason)
        return row


class SnoozeRecommendation:
    """M10.5 — postpone until ISO date."""

    def __init__(self, recommendations: RecommendationDomainService, authorization: AuthorizationPort) -> None:
        self._recommendations = recommendations
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        recommendation_id: str,
        *,
        actor_id: str,
        until: str,
    ) -> Recommendation:
        self._authorization.require_permission(ctx, "write")
        try:
            return self._recommendations.snooze_recommendation(
                ctx.tenant_id,
                recommendation_id,
                actor_id=actor_id,
                until=until,
            )
        except DecisionEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
