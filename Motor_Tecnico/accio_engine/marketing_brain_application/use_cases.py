from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_application.context import TenantContext
from Motor_Tecnico.accio_engine.decision_engine_application.errors import ApplicationError
from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapDomainService
from Motor_Tecnico.accio_engine.decision_engine_domain.errors import DailyRoadmapNotFound, DecisionEngineError
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.decision_engine_application.ports import AuthorizationPort
from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import EnrichmentParseError, LLMUnavailable, MarketingBrainError
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment, RoadmapEnrichmentResult
from Motor_Tecnico.accio_engine.marketing_brain_domain.service import MarketingBrainDomainService
from Motor_Tecnico.accio_engine.marketing_brain_infrastructure.memory_bridge import (
    record_daily_roadmap_enriched,
    record_recommendation_enriched,
)
from Motor_Tecnico.accio_engine.marketing_brain_infrastructure.roadmap_summary import build_ai_roadmap_summary
from Motor_Tecnico.accio_engine.memory_domain.service import CorporateMemoryDomainService
from Motor_Tecnico.accio_engine.platform_infrastructure.db import memory_sql_enabled


def _map_brain_error(exc: Exception) -> ApplicationError:
    if isinstance(exc, DecisionEngineError):
        return ApplicationError("not_found", str(exc), 404)
    if isinstance(exc, LLMUnavailable):
        return ApplicationError("llm_unavailable", str(exc), 503)
    if isinstance(exc, EnrichmentParseError):
        return ApplicationError("enrichment_parse_error", str(exc), 502)
    if isinstance(exc, MarketingBrainError):
        return ApplicationError("marketing_brain_error", str(exc), 500)
    raise exc


class EnrichRecommendation:
    """M11.1 — IA enriquece reason/description/confidence de una recomendación."""

    def __init__(
        self,
        brain: MarketingBrainDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._brain = brain
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(
        self,
        ctx: TenantContext,
        recommendation_id: str,
        *,
        persist: bool = False,
        actor_id: str = "system",
    ) -> tuple[Recommendation, RecommendationEnrichment]:
        self._authorization.require_permission(ctx, "write")
        try:
            rec, enrichment = self._brain.enrich(ctx.tenant_id, recommendation_id, persist=persist)
        except (DecisionEngineError, LLMUnavailable, EnrichmentParseError, MarketingBrainError) as exc:
            raise _map_brain_error(exc) from exc
        if persist:
            record_recommendation_enriched(
                self._memory,
                recommendation=rec,
                enrichment=enrichment,
                actor_id=actor_id,
            )
        return rec, enrichment


class EnrichDailyRoadmap:
    """M11.2–M11.3 — enriquece roadmap + Memory + summary."""

    def __init__(
        self,
        brain: MarketingBrainDomainService,
        roadmaps: DailyRoadmapDomainService,
        recommendations: RecommendationDomainService,
        authorization: AuthorizationPort,
        memory: CorporateMemoryDomainService | None = None,
    ) -> None:
        self._brain = brain
        self._roadmaps = roadmaps
        self._recommendations = recommendations
        self._authorization = authorization
        self._memory = memory if memory_sql_enabled() else None

    def __call__(
        self,
        ctx: TenantContext,
        roadmap_date: str,
        *,
        persist: bool = False,
        skip_enriched: bool = True,
        limit: int = 20,
        actor_id: str = "system",
    ) -> RoadmapEnrichmentResult:
        self._authorization.require_permission(ctx, "write")
        try:
            bundle = self._roadmaps.get_daily_roadmap(ctx.tenant_id, roadmap_date)
            result = self._brain.enrich_roadmap_bundle(
                bundle,
                persist=persist,
                skip_enriched=skip_enriched,
                limit=limit,
            )
            if not persist or result.enriched_count == 0:
                return result

            ai_summary = build_ai_roadmap_summary(result)
            updated_roadmap = self._roadmaps.apply_ai_enrichment_summary(
                ctx.tenant_id,
                bundle.roadmap.roadmap_id,
                ai_summary,
            )
            for item in result.items:
                if item.persisted and item.enrichment is not None:
                    rec = self._recommendations.get_recommendation(ctx.tenant_id, item.recommendation_id)
                    record_recommendation_enriched(
                        self._memory,
                        recommendation=rec,
                        enrichment=item.enrichment,
                        actor_id=actor_id,
                    )
            record_daily_roadmap_enriched(
                self._memory,
                roadmap=updated_roadmap,
                ai_summary=ai_summary,
                actor_id=actor_id,
            )
            return RoadmapEnrichmentResult(
                roadmap_id=result.roadmap_id,
                roadmap_date=result.roadmap_date,
                items=result.items,
                enriched_count=result.enriched_count,
                skipped_count=result.skipped_count,
                failed_count=result.failed_count,
                persisted=result.persisted,
                roadmap_summary=updated_roadmap.summary,
            )
        except DailyRoadmapNotFound as exc:
            raise ApplicationError("roadmap_not_found", str(exc), 404) from exc
        except LLMUnavailable as exc:
            raise ApplicationError("llm_unavailable", str(exc), 503) from exc
