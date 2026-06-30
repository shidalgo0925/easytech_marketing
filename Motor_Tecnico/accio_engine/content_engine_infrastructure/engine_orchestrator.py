"""Content Engine orchestration — campaign → content."""

from __future__ import annotations

from dataclasses import replace

from Motor_Tecnico.accio_engine.campaign_domain.engine_service import CampaignEngineService
from Motor_Tecnico.accio_engine.campaign_domain.errors import CampaignError
from Motor_Tecnico.accio_engine.content_engine_domain.content_builder import ContentBuilder
from Motor_Tecnico.accio_engine.content_engine_domain.content_explainability import build_content_explain
from Motor_Tecnico.accio_engine.content_engine_domain.content_planner import ContentPlanner
from Motor_Tecnico.accio_engine.content_engine_domain.engine_service import ContentEngineService
from Motor_Tecnico.accio_engine.content_engine_domain.errors import ContentEngineError
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.content_engine_infrastructure.content_llm_client import ContentEnrichmentLLM
from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder


class ContentEngineOrchestrator:
    def __init__(
        self,
        content: ContentEngineService,
        campaigns: CampaignEngineService,
        planner: ContentPlanner | None = None,
        builder: ContentBuilder | None = None,
        llm: ContentEnrichmentLLM | None = None,
    ) -> None:
        self._content = content
        self._campaigns = campaigns
        self._planner = planner or ContentPlanner()
        self._builder = builder or ContentBuilder()
        self._llm = llm or ContentEnrichmentLLM()

    def from_campaign(
        self,
        tenant_id: str,
        campaign_id: str,
        *,
        actor_id: str = "system",
        enrich: bool = False,
    ) -> ContentPiece:
        try:
            campaign = self._campaigns.get(tenant_id, campaign_id)
        except CampaignError as exc:
            raise ContentEngineError(str(exc)) from exc

        if campaign.status not in {"approved", "running", "scheduled"}:
            raise ContentEngineError(
                f"La campaña debe estar aprobada (estado actual: {campaign.status})"
            )

        existing = self._find_by_campaign(tenant_id, campaign_id)
        if existing:
            return existing

        ctx = get_marketing_context_builder().build(tenant_id, app_id=campaign.brand_id)
        plan = self._planner.plan(campaign, marketing_context=ctx)
        item = plan.items[0]
        piece = self._builder.build(tenant_id, campaign, plan, item)
        explain = build_content_explain(content=piece, campaign=campaign, plan=plan)
        piece = replace(piece, explain=explain)

        if enrich:
            piece = self.enrich_content(tenant_id, piece.content_id, piece=piece, actor_id=actor_id)

        saved = self._content.save(piece)
        self._content.record_created(saved, actor_id=actor_id)
        return saved

    def enrich_content(
        self,
        tenant_id: str,
        content_id: str,
        *,
        actor_id: str = "system",
        piece: ContentPiece | None = None,
    ) -> ContentPiece:
        row = piece or self._content.get(tenant_id, content_id)
        try:
            enrichment = self._llm.enrich_content(row)
            explain = dict(row.explain or {})
            explain["ai_enrichment"] = enrichment.to_dict()
            updated = replace(
                row,
                headline=enrichment.headline,
                body=enrichment.body,
                call_to_action=enrichment.call_to_action,
                hashtags=enrichment.hashtags or row.hashtags,
                llm_enrichment=enrichment.to_dict(),
                llm_skipped=False,
                explain=explain,
            )
        except Exception:
            updated = replace(row, llm_skipped=True)

        return self._content.save(updated)

    def _find_by_campaign(self, tenant_id: str, campaign_id: str) -> ContentPiece | None:
        rows = self._content.list_content(tenant_id, campaign_id=campaign_id, limit=5)
        return rows[0] if rows else None
