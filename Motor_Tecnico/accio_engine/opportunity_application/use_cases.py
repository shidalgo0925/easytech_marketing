from __future__ import annotations

from dataclasses import dataclass

from Motor_Tecnico.accio_engine.opportunity_application.context import TenantContext
from Motor_Tecnico.accio_engine.opportunity_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.opportunity_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.opportunity_domain.errors import OpportunityEngineError
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.opportunity_domain.promotion_service import OpportunityPromotionService, PromotionResult
from Motor_Tecnico.accio_engine.opportunity_infrastructure.intelligence_bridge import OpportunityIntelligenceBridge
from Motor_Tecnico.accio_engine.opportunity_infrastructure.intelligence_bridge import OpportunityIntelligenceBridge
from Motor_Tecnico.accio_engine.opportunity_infrastructure.knowledge_reader import CompositeOpportunityKnowledgeReader
from Motor_Tecnico.accio_engine.opportunity_domain.service import DetectionResult, OpportunityDetectionService
from Motor_Tecnico.accio_engine.opportunity_infrastructure.memory_bridge import (
    record_opportunity_dismissed,
    record_opportunity_identified,
    record_opportunity_promoted,
)
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled
from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext as DecisionTenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError as DecisionApplicationError
from Motor_Tecnico.accio_engine.decision_engine_application.use_cases import CreateRecommendationFromCandidate, GenerateDailyRoadmap
from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapBundle
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import tenant_today_iso
from Motor_Tecnico.accio_engine.marketing_brain_application.use_cases import EnrichDailyRoadmap
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RoadmapEnrichmentResult


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
        intelligence: OpportunityIntelligenceBridge,
        recommendations: RecommendationDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._promotion = promotion
        self._create_recommendation = create_recommendation
        self._intelligence = intelligence
        self._recommendations = recommendations
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(self, ctx: TenantContext, opportunity_id: str, *, actor_id: str = "system") -> PromotionResult:
        self._authorization.require_permission(ctx, "write")
        try:
            opp = self._promotion.require_promotable(ctx.tenant_id, opportunity_id)
            candidate, composed, score, explain = self._intelligence.compose_promotion(ctx.tenant_id, opp)
            recommendation = self._create_recommendation(
                DecisionTenantContext(tenant_id=ctx.tenant_id),
                candidate,
                created_by=actor_id,
            )
            recommendation = self._intelligence.attach_to_recommendation(
                recommendation,
                composed=composed,
                explain=explain,
                score=score,
            )
            self._recommendations.save_recommendation(recommendation)
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


@dataclass(frozen=True)
class MarketingPipelineStatus:
    detected: int
    promoted: int
    roadmap_generated: bool
    llm_enriched: int
    llm_skipped: bool
    llm_skip_reason: str | None
    errors: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True)
class MarketingPipelineResult:
    promote: DetectAndPromoteResult
    roadmap: DailyRoadmapBundle
    enrichment: RoadmapEnrichmentResult | None
    status: MarketingPipelineStatus


class RunMarketingPipeline:
    """F4 — detectar, promover, generar roadmap del día y enriquecer con IA (si disponible)."""

    def __init__(
        self,
        detect_and_promote: DetectAndPromoteOpportunities,
        generate_roadmap: GenerateDailyRoadmap,
        enrich_roadmap: EnrichDailyRoadmap,
        authorization: AuthorizationPort,
    ) -> None:
        self._detect_and_promote = detect_and_promote
        self._generate_roadmap = generate_roadmap
        self._enrich_roadmap = enrich_roadmap
        self._authorization = authorization

    def __call__(
        self,
        ctx: TenantContext,
        *,
        priority: str | None = "high",
        limit: int = 10,
        enrich: bool = True,
        actor_id: str = "system",
    ) -> MarketingPipelineResult:
        self._authorization.require_permission(ctx, "write")
        promote = self._detect_and_promote(
            ctx,
            priority=priority,
            limit=limit,
            actor_id=actor_id,
        )
        de_ctx = DecisionTenantContext(tenant_id=ctx.tenant_id)
        roadmap_date = tenant_today_iso()
        bundle = self._generate_roadmap(de_ctx, roadmap_date, created_by=actor_id)

        enrichment: RoadmapEnrichmentResult | None = None
        llm_skipped = False
        llm_skip_reason: str | None = None
        errors: list[dict[str, str]] = []
        if enrich:
            try:
                enrichment = self._enrich_roadmap(
                    de_ctx,
                    roadmap_date,
                    persist=True,
                    skip_enriched=True,
                    limit=max(1, min(limit, 20)),
                    actor_id=actor_id,
                )
            except DecisionApplicationError as exc:
                if exc.code != "llm_unavailable":
                    raise ApplicationError(exc.code, exc.message, exc.http_status) from exc
                llm_skipped = True
                llm_skip_reason = exc.message
                errors.append({"code": exc.code, "message": exc.message})

        from Motor_Tecnico.accio_engine.ai_provider import llm_unavailable_reason

        if enrich and llm_skipped and not llm_skip_reason:
            llm_skip_reason = llm_unavailable_reason() or "llm_unavailable"

        status = MarketingPipelineStatus(
            detected=promote.detection.created_count,
            promoted=promote.promoted_count,
            roadmap_generated=True,
            llm_enriched=enrichment.enriched_count if enrichment else 0,
            llm_skipped=llm_skipped if enrich else False,
            llm_skip_reason=llm_skip_reason if enrich and llm_skipped else None,
            errors=tuple(errors),
        )

        return MarketingPipelineResult(
            promote=promote,
            roadmap=bundle,
            enrichment=enrichment,
            status=status,
        )
