"""Content AI enrichment via Marketing Brain / AI Provider."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider
from Motor_Tecnico.accio_engine.content_engine_domain.model import ContentPiece
from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import EnrichmentParseError, LLMUnavailable
from Motor_Tecnico.accio_engine.marketing_context_engine import get_marketing_context_builder


@dataclass(frozen=True)
class ContentEnrichment:
    headline: str
    body: str
    call_to_action: str
    hashtags: tuple[str, ...]
    narrative: str = ""
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "headline": self.headline,
            "body": self.body,
            "call_to_action": self.call_to_action,
            "hashtags": list(self.hashtags),
            "narrative": self.narrative,
            "model": self.model,
        }


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise EnrichmentParseError("LLM response must be a JSON object")
    return payload


class ContentEnrichmentLLM:
    def enrich_content(self, piece: ContentPiece) -> ContentEnrichment:
        if not ai_provider.llm_available(piece.tenant_id, {}):
            raise LLMUnavailable("AI provider not configured or disabled")

        ctx = get_marketing_context_builder().build(piece.tenant_id, app_id=piece.brand_id)
        system = (
            "Eres el Marketing Brain de EM+Acción. Mejora el borrador estructurado de contenido. "
            "No cambies canal, formato ni tipo editorial. "
            "Responde SOLO JSON: headline, body, call_to_action, hashtags (array), narrative."
        )
        user = json.dumps({"marketing_context": ctx, "content": piece.to_api_dict(), "explain": piece.explain}, ensure_ascii=False)
        msg, model, _ = ai_provider.chat_completion(
            piece.tenant_id,
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.4,
        )
        content = (msg.get("content") or "").strip()
        if not content:
            raise EnrichmentParseError("Empty LLM response")
        payload = _extract_json(content)
        tags = payload.get("hashtags") or list(piece.hashtags)
        if isinstance(tags, str):
            tags = [tags]
        return ContentEnrichment(
            headline=str(payload.get("headline") or piece.headline).strip(),
            body=str(payload.get("body") or piece.body).strip(),
            call_to_action=str(payload.get("call_to_action") or piece.call_to_action).strip(),
            hashtags=tuple(str(t).strip() for t in tags if str(t).strip()),
            narrative=str(payload.get("narrative") or "").strip(),
            model=model,
        )
