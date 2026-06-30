from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapBundle
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import EnrichmentParseError, LLMUnavailable
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import (
    EnrichmentItemResult,
    RecommendationEnrichment,
    RoadmapEnrichmentResult,
)
from Motor_Tecnico.accio_engine.marketing_brain_domain.ports import MarketingBrainLLM


def _already_enriched(recommendation: Recommendation) -> bool:
    return bool((recommendation.justification_refs or {}).get("ai_enrichment"))


class MarketingBrainDomainService:
    """M11 — enriquece recomendaciones del Decision Engine con IA."""

    def __init__(
        self,
        llm: MarketingBrainLLM,
        recommendations: RecommendationDomainService,
    ) -> None:
        self._llm = llm
        self._recommendations = recommendations

    def enrich(
        self,
        tenant_id: str,
        recommendation_id: str,
        *,
        persist: bool = False,
    ) -> tuple[Recommendation, RecommendationEnrichment]:
        rec = self._recommendations.get_recommendation(tenant_id, recommendation_id)
        enrichment = self._llm.enrich_recommendation(rec)
        if persist:
            rec = self._recommendations.apply_enrichment(tenant_id, recommendation_id, enrichment)
        return rec, enrichment

    def enrich_roadmap_bundle(
        self,
        bundle: DailyRoadmapBundle,
        *,
        persist: bool = False,
        skip_enriched: bool = True,
        limit: int = 20,
    ) -> RoadmapEnrichmentResult:
        """M11.2 — enriquece todas las recomendaciones de un roadmap diario."""
        tenant_id = bundle.roadmap.tenant_id
        if not self._llm_available(tenant_id):
            raise LLMUnavailable("AI provider not configured or disabled")

        items: list[EnrichmentItemResult] = []
        enriched_count = 0
        skipped_count = 0
        failed_count = 0

        for rec in bundle.recommendations[: max(1, min(limit, 50))]:
            if skip_enriched and _already_enriched(rec):
                skipped_count += 1
                items.append(
                    EnrichmentItemResult(
                        recommendation_id=rec.recommendation_id,
                        recommendation=rec.to_api_dict(),
                        skipped=True,
                    )
                )
                continue
            try:
                enrichment = self._llm.enrich_recommendation(rec)
                updated = rec
                if persist:
                    updated = self._recommendations.apply_enrichment(
                        tenant_id,
                        rec.recommendation_id,
                        enrichment,
                    )
                enriched_count += 1
                items.append(
                    EnrichmentItemResult(
                        recommendation_id=rec.recommendation_id,
                        enrichment=enrichment,
                        recommendation=updated.to_api_dict(),
                        persisted=persist,
                    )
                )
            except (EnrichmentParseError, LLMUnavailable) as exc:
                failed_count += 1
                items.append(
                    EnrichmentItemResult(
                        recommendation_id=rec.recommendation_id,
                        recommendation=rec.to_api_dict(),
                        error=str(exc),
                    )
                )

        return RoadmapEnrichmentResult(
            roadmap_id=bundle.roadmap.roadmap_id,
            roadmap_date=bundle.roadmap.roadmap_date,
            items=items,
            enriched_count=enriched_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            persisted=persist,
        )

    def _llm_available(self, tenant_id: str) -> bool:
        from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider

        return ai_provider.llm_available(tenant_id, {})
