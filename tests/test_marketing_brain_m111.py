#!/usr/bin/env python3
"""Tests M11.1 Marketing Brain — enrich recommendation."""

from __future__ import annotations

import json
import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client import (  # noqa: E402
    AiProviderMarketingBrainLLM,
    _extract_json,
)


def _sample_rec() -> Recommendation:
    return Recommendation(
        tenant_id="easytech",
        recommendation_id="rec-test-1",
        company_id="easytech",
        brand_id="en1",
        title="Publicar en LinkedIn",
        action="create_publication",
        reason="Marca sin publicaciones recientes",
        priority="high",
        owner_role="marketing",
        source="brand_publication_gap",
        status="pending_approval",
        created_by="system",
        created_at="2026-06-26T12:00:00+00:00",
        updated_at="2026-06-26T12:00:00+00:00",
        description="Impulsar EN1 en LinkedIn",
        confidence=1.0,
    )


class MarketingBrainM111Tests(unittest.TestCase):
    def test_extract_json_plain(self):
        payload = _extract_json('{"reason":"x","confidence":0.8}')
        self.assertEqual(payload["reason"], "x")

    def test_extract_json_codeblock(self):
        payload = _extract_json('```json\n{"reason":"y","confidence":0.5}\n```')
        self.assertEqual(payload["reason"], "y")

    @mock.patch("Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client.ai_provider.chat_completion")
    @mock.patch("Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client.ai_provider.llm_available", return_value=True)
    def test_llm_enrich_parses_response(self, _avail, chat):
        chat.return_value = (
            {
                "content": json.dumps(
                    {
                        "reason": "EN1 necesita visibilidad B2B",
                        "description": "Post educativo sobre plataforma unificada",
                        "confidence": 0.82,
                        "narrative": "Priorizar martes 9am",
                    }
                )
            },
            "qwen2.5-coder:14b",
            None,
        )
        enrichment = AiProviderMarketingBrainLLM().enrich_recommendation(_sample_rec())
        self.assertIn("EN1", enrichment.reason)
        self.assertAlmostEqual(enrichment.confidence, 0.82)
        self.assertEqual(enrichment.model, "qwen2.5-coder:14b")

    @mock.patch("Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client.ai_provider.llm_available", return_value=False)
    def test_llm_unavailable_raises(self, _avail):
        from Motor_Tecnico.accio_engine.marketing_brain_domain.errors import LLMUnavailable

        with self.assertRaises(LLMUnavailable):
            AiProviderMarketingBrainLLM().enrich_recommendation(_sample_rec())

    def test_enrichment_to_dict(self):
        row = RecommendationEnrichment(
            reason="r",
            description="d",
            confidence=0.7,
            model="test-model",
            narrative="n",
        )
        self.assertEqual(row.to_dict()["model"], "test-model")

    @mock.patch("Motor_Tecnico.accio_engine.ai_provider.manager.llm_available", return_value=True)
    def test_enrich_roadmap_bundle_skips_enriched(self, _avail):
        from Motor_Tecnico.accio_engine.decision_engine_domain.daily_roadmap_service import DailyRoadmapBundle
        from Motor_Tecnico.accio_engine.decision_engine_domain.model import DailyRoadmap
        from Motor_Tecnico.accio_engine.decision_engine_domain.recommendation_service import RecommendationDomainService
        from Motor_Tecnico.accio_engine.marketing_brain_domain.service import MarketingBrainDomainService

        rec = _sample_rec()
        enriched = replace(rec, justification_refs={"ai_enrichment": {"model": "x"}})
        bundle = DailyRoadmapBundle(
            roadmap=DailyRoadmap(
                tenant_id="easytech",
                roadmap_id="rm-2026-06-26",
                company_id="easytech",
                roadmap_date="2026-06-26",
                generated_at="2026-06-26T12:00:00+00:00",
            ),
            recommendations=[rec, enriched],
        )

        class _FakeLLM:
            def enrich_recommendation(self, recommendation):
                return RecommendationEnrichment(
                    reason="new",
                    description="new",
                    confidence=0.9,
                    model="fake",
                )

        class _FakeRepo:
            def get(self, *a, **k):
                return None

            def save(self, *a, **k):
                pass

            def update(self, *a, **k):
                pass

            def list_recommendations(self, *a, **k):
                return []

        brain = MarketingBrainDomainService(_FakeLLM(), RecommendationDomainService(_FakeRepo()))
        result = brain.enrich_roadmap_bundle(bundle, persist=False, skip_enriched=True)
        self.assertEqual(result.skipped_count, 1)
        self.assertEqual(result.enriched_count, 1)


if __name__ == "__main__":
    unittest.main()
