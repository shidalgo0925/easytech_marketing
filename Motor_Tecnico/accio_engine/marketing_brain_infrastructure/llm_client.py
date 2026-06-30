"""Cliente LLM para Marketing Brain — usa Accio AI Provider Manager."""

from __future__ import annotations

import json
import re
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation
from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import EnrichmentParseError, LLMUnavailable
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment
from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnrichmentParseError(f"LLM response is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise EnrichmentParseError("LLM response must be a JSON object")
    return payload


def _clamp_confidence(value: Any, fallback: float) -> float:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(0.0, min(1.0, num))


class AiProviderMarketingBrainLLM:
    def enrich_recommendation(self, recommendation: Recommendation) -> RecommendationEnrichment:
        if not ai_provider.llm_available(recommendation.tenant_id, {}):
            raise LLMUnavailable("AI provider not configured or disabled")

        system = (
            "Eres el Marketing Brain de EM+Acción — Director de Marketing B2B Panamá/LATAM. "
            "Enriquece la recomendación operativa sin cambiar su acción ni prioridad. "
            "Usa el marketing_context para alinear tono, CTA y sector. "
            "Responde SOLO JSON válido con claves: reason, description, confidence (0-1), narrative."
        )
        marketing_context = get_marketing_context_builder().build_for_llm(
            recommendation.tenant_id,
            purpose="enrich",
            app_id=recommendation.brand_id,
        )
        user = json.dumps(
            {
                "marketing_context": marketing_context,
                "recommendation": {
                    "tenant_id": recommendation.tenant_id,
                    "brand_id": recommendation.brand_id,
                    "title": recommendation.title,
                    "action": recommendation.action,
                    "reason": recommendation.reason,
                    "description": recommendation.description,
                    "priority": recommendation.priority,
                    "priority_score": recommendation.priority_score,
                    "owner_role": recommendation.owner_role,
                    "source": recommendation.source,
                    "confidence": recommendation.confidence,
                    "justification_refs": recommendation.justification_refs,
                },
            },
            ensure_ascii=False,
        )
        msg, model, _cost = ai_provider.chat_completion(
            recommendation.tenant_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.35,
        )
        content = (msg.get("content") or "").strip()
        if not content:
            raise EnrichmentParseError("Empty LLM response")
        payload = _extract_json(content)
        return RecommendationEnrichment(
            reason=str(payload.get("reason") or recommendation.reason).strip(),
            description=str(payload.get("description") or recommendation.description).strip(),
            confidence=_clamp_confidence(payload.get("confidence"), recommendation.confidence),
            model=model,
            narrative=str(payload.get("narrative") or "").strip(),
        )
