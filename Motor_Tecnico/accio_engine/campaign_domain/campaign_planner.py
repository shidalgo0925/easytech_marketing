"""CampaignPlanner — planifica campaña desde recomendación + contexto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from Motor_Tecnico.accio_engine.campaign_domain.constants import CAMPAIGN_PLANNER_VERSION
from Motor_Tecnico.accio_engine.campaign_domain.model import CampaignChannel, CampaignKpi
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity

_ACTION_CAMPAIGN_TYPE = {
    "create_publication": "awareness",
    "resume_campaign": "retention",
    "follow_up_lead": "conversion",
    "publish": "awareness",
    "review_opportunity": "growth",
}

_ACTION_FREQUENCY = {
    "create_publication": "weekly",
    "resume_campaign": "biweekly",
    "follow_up_lead": "daily",
    "publish": "weekly",
}

_DEFAULT_KPIS = {
    "awareness": (
        CampaignKpi("reach", "Alcance estimado", target_value=500.0, unit="personas"),
        CampaignKpi("engagement", "Interacciones", target_value=25.0, unit="acciones"),
    ),
    "conversion": (
        CampaignKpi("leads", "Leads generados", target_value=5.0, unit="leads"),
        CampaignKpi("conversion_rate", "Tasa de conversión", target_value=0.08, unit="ratio"),
    ),
    "retention": (
        CampaignKpi("reactivation", "Cuentas reactivadas", target_value=3.0, unit="cuentas"),
    ),
    "growth": (
        CampaignKpi("pipeline", "Oportunidades en pipeline", target_value=2.0, unit="ops"),
    ),
}


@dataclass(frozen=True)
class CampaignPlan:
    objective: str
    target_audience: str
    priority: str
    channels: tuple[CampaignChannel, ...]
    call_to_action: str
    campaign_type: str
    frequency: str
    duration_days: int
    start_date: str
    end_date: str
    kpis: tuple[CampaignKpi, ...]
    estimated_reach: int
    estimated_leads: int
    estimated_conversion: float
    origin_score: float
    context_used: tuple[str, ...]
    planner_version: str = CAMPAIGN_PLANNER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "target_audience": self.target_audience,
            "priority": self.priority,
            "channels": [{"channel": c.channel, "role": c.role} for c in self.channels],
            "call_to_action": self.call_to_action,
            "campaign_type": self.campaign_type,
            "frequency": self.frequency,
            "duration_days": self.duration_days,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "kpis": [
                {"kpi_id": k.kpi_id, "name": k.name, "target_value": k.target_value, "unit": k.unit}
                for k in self.kpis
            ],
            "estimated_reach": self.estimated_reach,
            "estimated_leads": self.estimated_leads,
            "estimated_conversion": self.estimated_conversion,
            "origin_score": self.origin_score,
            "context_used": list(self.context_used),
            "planner_version": self.planner_version,
        }


class CampaignPlanner:
    def plan(
        self,
        recommendation: Recommendation,
        *,
        marketing_context: dict[str, Any] | None = None,
        opportunity: Opportunity | None = None,
    ) -> CampaignPlan:
        refs = recommendation.justification_refs or {}
        composed = recommendation.composed or {}
        explain = recommendation.explain or {}

        objective = str(composed.get("objective") or recommendation.reason or recommendation.title).strip()
        priority = str(composed.get("priority") or recommendation.priority or "medium")

        channel = str(
            refs.get("channel")
            or (opportunity.channel if opportunity else None)
            or "linkedin"
        ).lower()
        channels = (CampaignChannel(channel, "primary"),)

        campaign_type = _ACTION_CAMPAIGN_TYPE.get(recommendation.action, "awareness")
        frequency = _ACTION_FREQUENCY.get(recommendation.action, "weekly")

        cta = "DIAGNÓSTICO"
        matrix = refs.get("matrix") or (opportunity.payload or {}).get("matrix") if opportunity else None
        if isinstance(matrix, dict) and matrix.get("cta"):
            cta = str(matrix["cta"])
        elif marketing_context:
            brain = marketing_context.get("company_brain") or {}
            profile = brain.get("profile") or brain
            if isinstance(profile, dict) and profile.get("cta"):
                cta = str(profile["cta"])

        audience = self._audience(recommendation, opportunity, marketing_context)
        duration = self._duration(priority, campaign_type)
        start = datetime.now(timezone.utc).date()
        end = start + timedelta(days=duration)

        score = self._origin_score(recommendation, opportunity, explain)
        reach, leads, conversion = self._estimates(score, campaign_type, priority)

        kpis = _DEFAULT_KPIS.get(campaign_type, _DEFAULT_KPIS["awareness"])
        context_used = self._context_labels(marketing_context, opportunity, explain)

        return CampaignPlan(
            objective=objective,
            target_audience=audience,
            priority=priority,
            channels=channels,
            call_to_action=cta,
            campaign_type=campaign_type,
            frequency=frequency,
            duration_days=duration,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            kpis=kpis,
            estimated_reach=reach,
            estimated_leads=leads,
            estimated_conversion=conversion,
            origin_score=score,
            context_used=context_used,
        )

    def _audience(
        self,
        recommendation: Recommendation,
        opportunity: Opportunity | None,
        ctx: dict[str, Any] | None,
    ) -> str:
        sector = ""
        if opportunity and opportunity.sector:
            sector = opportunity.sector
        elif ctx:
            matrix = (ctx.get("knowledge_matrix") or {})
            sector = str(matrix.get("sector_label") or matrix.get("sector_id") or "")
        brand = recommendation.brand_id or "marca"
        if sector:
            return f"Decisores B2B en {sector} interesados en {brand}"
        return f"Empresas B2B en Panamá/LATAM — segmento {brand}"

    def _duration(self, priority: str, campaign_type: str) -> int:
        base = {"high": 21, "medium": 30, "low": 45}.get(priority, 30)
        if campaign_type == "conversion":
            return max(14, base - 7)
        return base

    def _origin_score(
        self,
        recommendation: Recommendation,
        opportunity: Opportunity | None,
        explain: dict[str, Any],
    ) -> float:
        if explain.get("score") is not None:
            return float(explain["score"])
        refs = recommendation.justification_refs or {}
        if refs.get("opportunity_score") is not None:
            return float(refs["opportunity_score"])
        if opportunity and opportunity.score:
            return float(opportunity.score)
        return round((recommendation.priority_score or 0.5) * 100, 2)

    def _estimates(self, score: float, campaign_type: str, priority: str) -> tuple[int, int, float]:
        factor = max(score / 100.0, 0.3)
        prio_mul = {"high": 1.3, "medium": 1.0, "low": 0.7}.get(priority, 1.0)
        reach = int(400 * factor * prio_mul)
        leads = int(8 * factor * prio_mul) if campaign_type in {"conversion", "growth"} else int(4 * factor)
        conversion = round(min(0.25, 0.05 + factor * 0.08), 3)
        return reach, leads, conversion

    def _context_labels(
        self,
        ctx: dict[str, Any] | None,
        opportunity: Opportunity | None,
        explain: dict[str, Any],
    ) -> tuple[str, ...]:
        labels: list[str] = []
        if ctx:
            if ctx.get("company_brain"):
                labels.append("company_brain")
            if ctx.get("knowledge_matrix"):
                labels.append("knowledge_matrix")
            if ctx.get("related_campaigns"):
                labels.append("related_campaigns")
            if ctx.get("recent_publications"):
                labels.append("recent_publications")
            if ctx.get("kpis"):
                labels.append("kpis")
        if opportunity:
            labels.append("opportunity_score")
        if explain:
            labels.append("recommendation_explain")
        if not labels:
            labels.append("recommendation_composed")
        return tuple(labels)
