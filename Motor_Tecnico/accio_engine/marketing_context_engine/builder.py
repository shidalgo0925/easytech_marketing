"""Marketing Context Engine — contexto estructurado único para IA y módulos EM+Acción."""

from __future__ import annotations

from typing import Any

from Motor_Tecnico.accio_engine import knowledge_api, marketing_app, settings_center
from Motor_Tecnico.accio_engine.brand_infrastructure.facade import get_brand_service
from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import get_company_brain_service
from Motor_Tecnico.accio_engine.decision_engine_api.composition import build_daily_roadmap_service, build_recommendation_service, roadmap_builder
from Motor_Tecnico.accio_engine.decision_engine_domain.errors import DailyRoadmapNotFound
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.roadmap_mapper import tenant_today_iso
from Motor_Tecnico.accio_engine.knowledge_matrix_api.composition import get_knowledge_matrix_service
from Motor_Tecnico.accio_engine.marketing_context_engine.constants import (
    COMMERCIAL_CTA,
    COMMERCIAL_GUIDE_URL,
    EDITORIAL_RULE_LABEL,
)
from Motor_Tecnico.accio_engine.opportunity_infrastructure.sqlite_repository import SqliteOpportunityRepository


class MarketingContextBuilder:
    """Reúne señales de negocio y estado operativo en un contexto estructurado por tenant."""

    def __init__(
        self,
        *,
        opportunity_repo: SqliteOpportunityRepository | None = None,
    ) -> None:
        self._opportunities = opportunity_repo or SqliteOpportunityRepository()

    def build(
        self,
        tenant_id: str,
        *,
        app_id: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
        brain = get_company_brain_service().get_or_empty(tenant_id)
        brands = get_brand_service().list_brands(tenant_id, active_only=True)
        products = settings_center.load_products(tenant_id).get("products", [])
        editorial = knowledge_api.load_editorial_rules(tenant_id)
        matrix = get_knowledge_matrix_service().get_matrix(tenant_id)

        opportunities = [
            row.to_api_dict()
            for row in self._opportunities.list_opportunities(
                tenant_id,
                status="detected",
                limit=limit,
            )
        ]
        recommendations = [
            rec.to_api_dict()
            for rec in build_recommendation_service().list_recommendations(
                tenant_id,
                status="pending_approval",
                limit=limit,
            )
        ]

        roadmap_today = None
        try:
            bundle = build_daily_roadmap_service(roadmap_builder()).get_daily_roadmap(
                tenant_id,
                tenant_today_iso(),
            )
            roadmap_today = bundle.roadmap.to_api_dict(recommendations=bundle.recommendations)
        except DailyRoadmapNotFound:
            roadmap_today = None

        return {
            "tenant_id": tenant_id,
            "app_id": aid,
            "company_brain": brain.profile if brain else knowledge_api.load_business_context(tenant_id),
            "brands": [b.to_api_dict() for b in brands],
            "products_services": products,
            "knowledge_matrix": matrix.to_dict(),
            "opportunities_detected": opportunities,
            "recommendations_pending": recommendations,
            "roadmap_today": roadmap_today,
            "editorial": {
                "rule": EDITORIAL_RULE_LABEL,
                "interim_rule": editorial.get("interim_rule"),
                "target_matrix": editorial.get("target_matrix"),
                "weekly_slots": editorial.get("weekly_slots"),
            },
            "commercial": {
                "cta": COMMERCIAL_CTA,
                "guide_url": COMMERCIAL_GUIDE_URL,
            },
            "builder_version": "marketing-context-engine-v1",
        }

    def build_for_llm(
        self,
        tenant_id: str,
        *,
        purpose: str = "enrich",
        app_id: str | None = None,
        limit: int = 12,
    ) -> dict[str, Any]:
        full = self.build(tenant_id, app_id=app_id, limit=limit)
        brain = full.get("company_brain") or {}
        return {
            "tenant_id": full["tenant_id"],
            "app_id": full["app_id"],
            "purpose": purpose,
            "company": {
                "name": brain.get("empresa") or brain.get("nombre_empresa"),
                "industry": brain.get("industria"),
                "audience": brain.get("publico_objetivo"),
                "products_services": brain.get("productos_servicios") or full.get("products_services"),
                "tone": brain.get("tono"),
            },
            "brands": [
                {"brand_id": b.get("brand_id"), "name": b.get("name"), "slug": b.get("slug")}
                for b in full.get("brands", [])[:8]
            ],
            "knowledge_matrix": full.get("knowledge_matrix"),
            "opportunities_detected": full.get("opportunities_detected", [])[:6],
            "recommendations_pending": full.get("recommendations_pending", [])[:6],
            "roadmap_today": {
                "roadmap_date": (full.get("roadmap_today") or {}).get("roadmap_date"),
                "summary": (full.get("roadmap_today") or {}).get("summary"),
                "recommendation_count": len((full.get("roadmap_today") or {}).get("recommendations") or []),
            },
            "editorial": full.get("editorial"),
            "commercial": full.get("commercial"),
        }


_BUILDER: MarketingContextBuilder | None = None


def get_marketing_context_builder() -> MarketingContextBuilder:
    global _BUILDER
    if _BUILDER is None:
        _BUILDER = MarketingContextBuilder()
    return _BUILDER


def reset_marketing_context_builder() -> None:
    global _BUILDER
    _BUILDER = None
