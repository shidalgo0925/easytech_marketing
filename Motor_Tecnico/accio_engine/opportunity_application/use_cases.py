from __future__ import annotations

from dataclasses import dataclass

from Motor_Tecnico.accio_engine.opportunity_application.context import TenantContext
from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.opportunity_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.opportunity_domain.errors import OpportunityEngineError
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.opportunity_domain.promotion_service import OpportunityPromotionService, PromotionResult
from Motor_Tecnico.accio_engine.opportunity_domain.service import DetectionResult, OpportunityDetectionService
from Motor_Tecnico.accio_engine.opportunity_infrastructure.memory_bridge import (
    record_opportunity_dismissed,
    record_opportunity_identified,
    record_opportunity_promoted,
)
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext as DecisionTenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.use_cases import CreateRecommendationFromCandidate


class DetectOpportunities:
    def __init__(
        self,
        detector: OpportunityDetectionService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._detector = detector
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, *, actor_id: str = "system") -> DetectionResult:
        self._authorization.require_permission(ctx, "write")
        result = self._detector.detect(ctx.tenant_id)
        for item in result.items:
            record_opportunity_identified(
                self._memory,
                opportunity=item.opportunity,
                actor_id=actor_id,
                created=item.created,
            )
        return result


class ListOpportunities:
    def __init__(self, detector: OpportunityDetectionService, authorization: AuthorizationPort) -> None:
        self._detector = detector
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        brand_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Opportunity]:
        self._authorization.require_permission(ctx, "read")
        return self._detector.list_opportunities(
            ctx.tenant_id,
            brand_id=brand_id,
            status=status,
            limit=limit,
        )


class GetOpportunity:
    def __init__(self, detector: OpportunityDetectionService, authorization: AuthorizationPort) -> None:
        self._detector = detector
        self._authorization = authorization

    def __call__(self, ctx: TenantContext, opportunity_id: str) -> Opportunity:
        self._authorization.require_permission(ctx, "read")
        try:
            return self._detector.get_opportunity(ctx.tenant_id, opportunity_id)
        except OpportunityEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc


class PromoteOpportunity:
    """F2 — oportunidad detectada → Recommendation pending_approval."""

    def __init__(
        self,
        promotion: OpportunityPromotionService,
        create_recommendation: CreateRecommendationFromCandidate,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._promotion = promotion
        self._create_recommendation = create_recommendation
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, opportunity_id: str, *, actor_id: str = "system") -> PromotionResult:
        self._authorization.require_permission(ctx, "write")
        try:
            _opp, candidate = self._promotion.to_candidate(ctx.tenant_id, opportunity_id)
            recommendation = self._create_recommendation(
                DecisionTenantContext(tenant_id=ctx.tenant_id),
                candidate,
                created_by=actor_id,
            )
            opportunity = self._promotion.mark_promoted(ctx.tenant_id, opportunity_id, recommendation)
        except OpportunityEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        record_opportunity_promoted(
            self._memory,
            opportunity=opportunity,
            recommendation_id=recommendation.recommendation_id,
            actor_id=actor_id,
        )
        return PromotionResult(opportunity=opportunity, recommendation=recommendation)


class DismissOpportunity:
    def __init__(
        self,
        promotion: OpportunityPromotionService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._promotion = promotion
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, opportunity_id: str, *, actor_id: str = "system") -> Opportunity:
        self._authorization.require_permission(ctx, "write")
        try:
            opportunity = self._promotion.dismiss(ctx.tenant_id, opportunity_id)
        except OpportunityEngineError as exc:
            raise ApplicationError.from_domain(exc) from exc
        record_opportunity_dismissed(self._memory, opportunity=opportunity, actor_id=actor_id)
        return opportunity


@dataclass(frozen=True)
class DetectAndPromoteResult:
    detection: DetectionResult
    promoted: list[PromotionResult]
    promoted_count: int
    skipped_count: int


class DetectAndPromoteOpportunities:
    """F3 — detecta y promueve oportunidades por prioridad."""

    def __init__(
        self,
        detect: DetectOpportunities,
        promote: PromoteOpportunity,
        authorization: AuthorizationPort,
    ) -> None:
        self._detect = detect
        self._promote = promote
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        priority: str | None = "high",
        limit: int = 10,
        actor_id: str = "system",
    ) -> DetectAndPromoteResult:
        self._authorization.require_permission(ctx, "write")
        detection = self._detect(ctx, actor_id=actor_id)
        promoted: list[PromotionResult] = []
        skipped = 0
        cap = max(1, min(limit, 20))
        for item in detection.items:
            if not item.created:
                skipped += 1
                continue
            if priority and item.opportunity.priority != priority:
                skipped += 1
                continue
            if item.opportunity.status != "detected":
                skipped += 1
                continue
            if len(promoted) >= cap:
                skipped += 1
                continue
            promoted.append(
                self._promote(ctx, item.opportunity.opportunity_id, actor_id=actor_id)
            )
        return DetectAndPromoteResult(
            detection=detection,
            promoted=promoted,
            promoted_count=len(promoted),
            skipped_count=skipped,
        )
