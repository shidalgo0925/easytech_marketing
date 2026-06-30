"""Campaign AI enrichment — Marketing Brain → AI Provider."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign
from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import EnrichmentParseError, LLMUnavailable
from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder


@dataclass(frozen=True)
class CampaignEnrichment:
    description: str
    main_message: str
    value_proposition: str
    additional_recommendations: tuple[str, ...]
    risks: tuple[str, ...]
    opportunities: tuple[str, ...]
    model: str = ""
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "main_message": self.main_message,
            "value_proposition": self.value_proposition,
            "additional_recommendations": list(self.additional_recommendations),
            "risks": list(self.risks),
            "opportunities": list(self.opportunities),
            "model": self.model,
            "narrative": self.narrative,
        }


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


def _as_str_list(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if isinstance(value, list):
        return tuple(str(v).strip() for v in value if str(v).strip())
    return ()


class CampaignEnrichmentLLM:
    """Enriquece campaña estructurada — no la crea desde cero."""

    def enrich_campaign(self, campaign: Campaign) -> CampaignEnrichment:
        if not ai_provider.llm_available(campaign.tenant_id, {}):
            raise LLMUnavailable("AI provider not configured or disabled")

        marketing_context = get_marketing_context_builder().build(
            campaign.tenant_id,
            app_id=campaign.brand_id,
        )
        system = (
            "Eres el Marketing Brain de EM+Acción. Enriquece la campaña estructurada existente. "
            "NO cambies objetivo, canales, CTA ni prioridad. "
            "Responde SOLO JSON con claves: description, main_message, value_proposition, "
            "additional_recommendations (array), risks (array), opportunities (array), narrative."
        )
        user = json.dumps(
            {
                "marketing_context": marketing_context,
                "campaign": campaign.to_api_dict(),
                "explain": campaign.explain,
            },
            ensure_ascii=False,
        )
        msg, model, _cost = ai_provider.chat_completion(
            campaign.tenant_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.35,
        )
        content = (msg.get("content") or "").strip()
        if not content:
            raise EnrichmentParseError("Empty LLM response")
        payload = _extract_json(content)
        return CampaignEnrichment(
            description=str(payload.get("description") or campaign.description).strip(),
            main_message=str(payload.get("main_message") or campaign.objective).strip(),
            value_proposition=str(payload.get("value_proposition") or campaign.value_proposition).strip(),
            additional_recommendations=_as_str_list(payload.get("additional_recommendations")),
            risks=_as_str_list(payload.get("risks")),
            opportunities=_as_str_list(payload.get("opportunities")),
            model=model,
            narrative=str(payload.get("narrative") or "").strip(),
        )
