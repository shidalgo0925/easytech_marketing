"""RecommendationComposer — oportunidad → recomendación ejecutiva estructurada."""

from __future__ import annotations

from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.model import (
    ComposedRecommendation,
    OpportunityScoreResult,
    RECOMMENDATION_COMPOSER_VERSION,
)
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity

_ACTION_BY_SIGNAL = {
    "brand_inactive": "create_publication",
    "campaign_stalled": "resume_campaign",
    "lead_followup_gap": "follow_up_lead",
}

_OBJECTIVE_BY_SIGNAL = {
    "brand_inactive": "Recuperar visibilidad y recordatorio de marca en canales digitales",
    "campaign_stalled": "Reactivar campaña estancada para no perder momentum comercial",
    "lead_followup_gap": "Cerrar brecha de seguimiento comercial con leads calificados",
}

_IMPACT_BY_SIGNAL = {
    "brand_inactive": "Mayor presencia de marca y oportunidades de contacto en el corto plazo",
    "campaign_stalled": "Recuperación de pipeline y continuidad del embudo de conversión",
    "lead_followup_gap": "Reducción de leads fríos y mejora en tasa de respuesta comercial",
}


class RecommendationComposer:
    def compose(
        self,
        opportunity: Opportunity,
        score: OpportunityScoreResult,
    ) -> ComposedRecommendation:
        action = _ACTION_BY_SIGNAL.get(opportunity.signal_type, "review_opportunity")
        objective = _OBJECTIVE_BY_SIGNAL.get(opportunity.signal_type, opportunity.need or "Mejorar desempeño comercial")
        impact = _IMPACT_BY_SIGNAL.get(opportunity.signal_type, "Impacto positivo en visibilidad y conversión")

        evidence: list[dict] = [
            {"type": "rule", "id": opportunity.signal_type, "label": f"Regla {opportunity.signal_type}"},
            {"type": "score", "value": score.score, "priority": score.priority},
            {"type": "brand", "brand_id": opportunity.brand_id, "product_slug": opportunity.product_slug},
        ]
        payload = opportunity.payload or {}
        if payload.get("gap_days") is not None:
            evidence.append({"type": "metric", "name": "gap_days", "value": payload["gap_days"]})
        if payload.get("lead_count") is not None:
            evidence.append({"type": "metric", "name": "lead_count", "value": payload["lead_count"]})
        if payload.get("matrix"):
            evidence.append({"type": "knowledge_matrix", "value": payload["matrix"]})

        reasons = list(score.reasoning)
        if opportunity.need:
            reasons.insert(0, opportunity.need)

        next_steps = self._next_steps(opportunity, action)

        return ComposedRecommendation(
            title=opportunity.title,
            description=opportunity.description,
            objective=objective,
            expected_impact=impact,
            recommended_action=action,
            priority=score.priority,
            reasons=tuple(reasons),
            evidence=tuple(evidence),
            next_steps=tuple(next_steps),
            composer_version=RECOMMENDATION_COMPOSER_VERSION,
        )

    def to_candidate(
        self,
        opportunity: Opportunity,
        composed: ComposedRecommendation,
        score: OpportunityScoreResult,
    ) -> RecommendationCandidate:
        refs = {
            "opportunity_id": opportunity.opportunity_id,
            "signal_key": opportunity.signal_key,
            "signal_type": opportunity.signal_type,
            "product_slug": opportunity.product_slug,
            "sector": opportunity.sector,
            "channel": opportunity.channel,
            "landing_url": opportunity.landing_url,
            "opportunity_score": score.score,
            "score_factors": score.factors,
        }
        refs.update(opportunity.payload or {})
        return RecommendationCandidate(
            brand_id=opportunity.brand_id,
            title=composed.title,
            description=composed.description,
            action=composed.recommended_action,
            reason=composed.objective,
            priority=composed.priority,
            priority_score=score.score / 100.0,
            owner_role="marketing",
            source=f"opportunity:{opportunity.signal_type}",
            confidence=score.confidence,
            justification_refs=refs,
        )

    def _next_steps(self, opportunity: Opportunity, action: str) -> list[str]:
        steps = ["Revisar evidencias en el panel «Por qué recomendamos esto»"]
        if action == "create_publication":
            steps.append(f"Preparar publicación para {opportunity.brand_id} en {opportunity.channel or 'LinkedIn'}")
        elif action == "resume_campaign":
            steps.append("Revisar campaña estancada y definir siguiente hito")
        elif action == "follow_up_lead":
            steps.append("Asignar seguimiento a leads sin contacto reciente")
        steps.append("Aprobar la recomendación para ejecutar en operaciones")
        return steps
