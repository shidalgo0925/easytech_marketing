"""Campaign Engine orchestration — from recommendation to campaign."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.campaign_builder import CampaignBuilder
from Motor_Tecnico.accio_engine.campaign_domain.campaign_explainability import build_campaign_explain
from Motor_Tecnico.accio_engine.campaign_domain.campaign_planner import CampaignPlanner
from Motor_Tecnico.accio_engine.campaign_domain.engine_service import CampaignEngineService
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.campaign_infrastructure.campaign_llm_client import CampaignEnrichmentLLM
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder
from Motor_Tecnico.accio_engine.opportunity_domain.service import OpportunityDetectionService


class CampaignEngineOrchestrator:
    def __init__(
        self,
        engine: CampaignEngineService,
        recommendations: RecommendationDomainService,
        opportunities: OpportunityDetectionService | None = None,
        planner: CampaignPlanner | None = None,
        builder: CampaignBuilder | None = None,
        llm: CampaignEnrichmentLLM | None = None,
    ) -> None:
        self._engine = engine
        self._recommendations = recommendations
        self._opportunities = opportunities
        self._planner = planner or CampaignPlanner()
        self._builder = builder or CampaignBuilder()
        self._llm = llm or CampaignEnrichmentLLM()

    def from_recommendation(
        self,
        tenant_id: str,
        recommendation_id: str,
        *,
        actor_id: str = "system",
        enrich: bool = False,
    ) -> Campaign:
        rec = self._recommendations.get_recommendation(tenant_id, recommendation_id)
        if rec.status != "approved":
            from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError

            raise CampaignError(
                f"La recomendación debe estar aprobada (estado actual: {rec.status})"
            )

        existing = self._find_by_recommendation(tenant_id, recommendation_id)
        if existing:
            return existing

        opportunity = self._load_opportunity(tenant_id, rec)
        ctx = get_marketing_context_builder().build_for_recommendation(tenant_id, rec)
        plan = self._planner.plan(rec, marketing_context=ctx, opportunity=opportunity)
        campaign = self._builder.build(
            tenant_id,
            rec,
            plan,
            origin_score=plan.origin_score,
        )
        explain = build_campaign_explain(
            campaign=campaign,
            recommendation=rec,
            plan=plan,
            opportunity=opportunity,
            marketing_context=ctx,
        )
        campaign = replace(campaign, explain=explain, origin_score=plan.origin_score)

        if enrich:
            campaign = self.enrich_campaign(tenant_id, campaign.campaign_id, actor_id=actor_id, campaign=campaign)

        saved = self._engine.save(campaign)
        self._engine.record_created(saved, actor_id=actor_id)
        return saved

    def enrich_campaign(
        self,
        tenant_id: str,
        campaign_id: str,
        *,
        actor_id: str = "system",
        campaign: Campaign | None = None,
    ) -> Campaign:
        row = campaign or self._engine.get(tenant_id, campaign_id)
        skipped = False
        enrichment_dict: dict[str, Any] | None = None
        updated = row
        try:
            enrichment = self._llm.enrich_campaign(row)
            enrichment_dict = enrichment.to_dict()
            explain = dict(row.explain or {})
            explain["ai_enrichment"] = enrichment_dict
            updated = replace(
                row,
                description=enrichment.description or row.description,
                value_proposition=enrichment.value_proposition or row.value_proposition,
                llm_enrichment=enrichment_dict,
                llm_skipped=False,
                explain=explain,
            )
        except Exception:
            skipped = True
            updated = replace(row, llm_skipped=True)

        saved = self._engine.save(updated)
        self._engine.record_enriched(saved, actor_id=actor_id, skipped=skipped)
        return saved

    def _load_opportunity(self, tenant_id: str, rec: Recommendation):
        if not self._opportunities:
            return None
        opp_id = (rec.justification_refs or {}).get("opportunity_id")
        if not opp_id:
            return None
        try:
            return self._opportunities.get_opportunity(tenant_id, str(opp_id))
        except Exception:
            return None

    def _find_by_recommendation(self, tenant_id: str, recommendation_id: str) -> Campaign | None:
        for row in self._engine.list_campaigns(tenant_id, limit=100):
            if row.recommendation_id == recommendation_id:
                return row
        return None
