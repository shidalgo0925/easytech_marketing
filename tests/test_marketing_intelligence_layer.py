#!/usr/bin/env python3
"""Tests Marketing Intelligence Layer — scorer, composer, explainability, API v2."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.app import app  # noqa: E402
from Motor_Tecnico.accio_engine.brand_domain.model import Brand  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.explainability import build_explain  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.opportunity_scorer import OpportunityScorer  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_intelligence_domain.recommendation_composer import RecommendationComposer  # noqa: E402
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity, OpportunityCandidate  # noqa: E402
from Motor_Tecnico.accio_engine.opportunity_domain.snapshot import OpportunitySnapshot  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _snapshot() -> OpportunitySnapshot:
    brand = Brand(
        brand_id="b_en1",
        tenant_id="easytech",
        company_id="easytech",
        name="EN1",
        slug="en1",
        legacy_app_id="en1",
        status="active",
    )
    brain = CompanyBrain(
        tenant_id="easytech",
        company_id="easytech",
        profile={"productos_servicios": ["EN1", "EPOSOne"]},
        status="published",
        updated_at="2026-06-01T00:00:00+00:00",
    )
    return OpportunitySnapshot(
        tenant_id="easytech",
        company_id="easytech",
        generated_at=datetime.now(timezone.utc).isoformat(),
        brands=(brand,),
        company_brain=brain,
    )


class OpportunityScorerTests(unittest.TestCase):
    def test_score_candidate_range(self) -> None:
        scorer = OpportunityScorer()
        candidate = OpportunityCandidate(
            signal_key="brand_inactive:en1",
            signal_type="brand_inactive",
            brand_id="en1",
            title="Marca inactiva",
            description="Sin actividad",
            sector="B2B",
            need="Visibilidad",
            product_slug="en1",
            channel="linkedin",
            landing_url="https://example.com",
            priority="high",
            source="brand_inactive",
            payload={"gap_days": 21},
        )
        result = scorer.score_candidate(candidate, _snapshot())
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 100)
        self.assertIn(result.priority, {"high", "medium", "low"})
        self.assertGreater(len(result.reasoning), 0)


class RecommendationComposerTests(unittest.TestCase):
    def test_compose_structure(self) -> None:
        scorer = OpportunityScorer()
        composer = RecommendationComposer()
        opp = Opportunity(
            tenant_id="easytech",
            opportunity_id="opp_test",
            signal_key="brand_inactive:en1",
            signal_type="brand_inactive",
            brand_id="en1",
            title="Marca inactiva — EN1",
            description="Sin publicaciones",
            sector="B2B",
            need="Visibilidad",
            product_slug="en1",
            channel="linkedin",
            landing_url="https://n8n.etsrv.site/guia/",
            priority="high",
            status="detected",
            source="brand_inactive",
            confidence=0.8,
            detected_at="2026-06-01T00:00:00+00:00",
            updated_at="2026-06-01T00:00:00+00:00",
            score=72.0,
            payload={"gap_days": 21},
        )
        score = scorer.score_opportunity(opp, _snapshot())
        composed = composer.compose(opp, score)
        self.assertIn("objective", composed.to_dict())
        self.assertGreater(len(composed.evidence), 0)
        candidate = composer.to_candidate(opp, composed, score)
        self.assertEqual(candidate.brand_id, "en1")
        explain = build_explain(opportunity=opp, score=score, composed=composed)
        self.assertIn("rules_triggered", explain.to_dict())


class IntelligenceAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="mil_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_CAMPAIGN_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        matrix_path = Path(self.tmp) / "Marketing" / "knowledge" / "sectors.json"
        matrix_path.parent.mkdir(parents=True)
        shutil.copy(BASE / "Marketing" / "knowledge" / "sectors.json", matrix_path)

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"productos_servicios": ["EN1"]}),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_app_id": "default",
                    "apps": [
                        {"app_id": "default", "name": "EasyTech", "slug": "default", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "slug": "en1", "status": "active", "is_default": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        en1_queue = {
            "posts": [
                {
                    "id": "linkedin_old_en1",
                    "platform": "linkedin",
                    "status": "published",
                    "published_at": "2026-05-01T10:00:00-05:00",
                    "text": "Post antiguo",
                    "app_id": "en1",
                }
            ]
        }
        (apps_dir / "en1" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "en1" / "content_queue.json").write_text(json.dumps(en1_queue), encoding="utf-8")
        (apps_dir / "default" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "default" / "content_queue.json").write_text(json.dumps({"posts": []}), encoding="utf-8")

        ensure_schema()
        self._reset()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            return {"content_queue": root / "content_queue.json", "campaigns": root / "campaigns.json"}

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", side_effect=lambda t: _paths(t.tenant_id)),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.marketing_app.effective_app_paths", _app_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.default_app_id", return_value="default"),
            patch("Motor_Tecnico.accio_engine.marketing_app.normalize_app_id", side_effect=lambda x: x or "default"),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.resolve_tenant",
                return_value=tenant_obj,
            ),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.effective_paths",
                side_effect=lambda t: _paths(t.tenant_id),
            ),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch("Motor_Tecnico.accio_engine.knowledge_matrix_infrastructure.json_repository.BASE_DIR", Path(self.tmp)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@mil"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def _reset(self) -> None:
        from Motor_Tecnico.accio_engine.brand_infrastructure.facade import reset_brand_service
        from Motor_Tecnico.accio_engine.campaign_infrastructure.facade import reset_campaign_service
        from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import reset_company_brain_service
        from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine_use_cases
        from Motor_Tecnico.accio_engine.decision_engine_api.routes import reset_use_cases_cache as reset_de_cache
        from Motor_Tecnico.accio_engine.knowledge_matrix_api.composition import reset_knowledge_matrix_service, reset_knowledge_matrix_use_cases
        from Motor_Tecnico.accio_engine.lead_infrastructure.facade import reset_lead_service
        from Motor_Tecnico.accio_engine.marketing_intelligence_api.routes import reset_intelligence_use_cases
        from Motor_Tecnico.accio_engine.opportunity_api.composition import reset_opportunity_use_cases
        from Motor_Tecnico.accio_engine.opportunity_api.routes import reset_use_cases_cache
        from Motor_Tecnico.accio_engine.publication_infrastructure.facade import reset_publication_service

        reset_brand_service()
        reset_publication_service()
        reset_campaign_service()
        reset_company_brain_service()
        reset_lead_service()
        reset_decision_engine_use_cases()
        reset_de_cache()
        reset_knowledge_matrix_service()
        reset_knowledge_matrix_use_cases()
        reset_opportunity_use_cases()
        reset_use_cases_cache()
        reset_intelligence_use_cases()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self._reset()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_schema_v13(self) -> None:
        conn = get_connection()
        try:
            versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
            cols = {r[1] for r in conn.execute("PRAGMA table_info(opportunities)")}
        finally:
            conn.close()
        self.assertIn(13, versions)
        self.assertIn("score", cols)

    def test_promote_has_explain(self) -> None:
        detect = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        self.assertEqual(detect.status_code, 201, detect.get_data(as_text=True))
        opp_id = detect.get_json()["data"]["opportunities"][0]["opportunity_id"]
        self.assertGreater(detect.get_json()["data"]["opportunities"][0]["score"], 0)

        promote = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}/promote")
        self.assertIn(promote.status_code, (200, 201), promote.get_data(as_text=True))
        rec_id = promote.get_json()["data"]["recommendation"]["recommendation_id"]

        explain = self.client.get(f"/api/v1/tenants/{self.tenant_id}/recommendations/{rec_id}/explain")
        self.assertEqual(explain.status_code, 200, explain.get_data(as_text=True))
        body = explain.get_json()["data"]
        self.assertIn("explain", body)
        self.assertIn("rules_triggered", body["explain"])


if __name__ == "__main__":
    unittest.main()
