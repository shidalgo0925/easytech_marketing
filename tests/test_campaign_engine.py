#!/usr/bin/env python3
"""Tests Campaign Engine — builder, planner, explain, API, persistence."""

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
from Motor_Tecnico.accio_engine.brand_infrastructure.facade import reset_brand_service  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_api.composition import reset_campaign_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_domain.campaign_builder import CampaignBuilder  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_domain.campaign_explainability import build_campaign_explain  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_domain.campaign_planner import CampaignPlanner  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_domain.model import Recommendation  # noqa: E402
from Motor_Tecnico.accio_engine.opportunity_domain.model import Opportunity  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _sample_recommendation(**overrides) -> Recommendation:
    now = datetime.now(timezone.utc).isoformat()
    base = dict(
        tenant_id="easytech",
        recommendation_id="rec_camp_test",
        company_id="easytech",
        brand_id="en1",
        title="Impulsar EN1",
        action="create_publication",
        reason="Recuperar visibilidad",
        priority="high",
        owner_role="marketing",
        source="opportunity:brand_inactive",
        status="approved",
        created_by="test",
        created_at=now,
        updated_at=now,
        description="Marca inactiva en EN1",
        priority_score=0.78,
        confidence=0.8,
        composed={
            "title": "Impulsar EN1",
            "objective": "Recuperar visibilidad digital",
            "expected_impact": "Mayor alcance",
            "priority": "high",
            "reasons": ["14 días sin publicación"],
        },
        explain={
            "score": 72.0,
            "rules_triggered": [{"signal_type": "brand_inactive"}],
            "reasoning": ["Prioridad alta por inactividad"],
            "factors": {"age": 0.47},
        },
        justification_refs={"opportunity_id": "opp_en1", "channel": "linkedin", "opportunity_score": 72.0},
    )
    base.update(overrides)
    return Recommendation(**base)


class CampaignPlannerTests(unittest.TestCase):
    def test_plan_structure(self) -> None:
        rec = _sample_recommendation()
        plan = CampaignPlanner().plan(rec, marketing_context={"company_brain": {"profile": {}}})
        self.assertIn(plan.campaign_type, {"awareness", "retention", "conversion", "growth"})
        self.assertGreater(len(plan.channels), 0)
        self.assertGreater(plan.origin_score, 0)
        self.assertGreater(len(plan.kpis), 0)


class CampaignBuilderTests(unittest.TestCase):
    def test_build_campaign(self) -> None:
        rec = _sample_recommendation()
        planner = CampaignPlanner()
        plan = planner.plan(rec)
        campaign = CampaignBuilder().build("easytech", rec, plan, origin_score=plan.origin_score)
        self.assertTrue(campaign.campaign_id.startswith("cmp_"))
        self.assertEqual(campaign.recommendation_id, "rec_camp_test")
        self.assertEqual(campaign.status, "draft")
        self.assertEqual(campaign.objective, plan.objective)


class CampaignExplainTests(unittest.TestCase):
    def test_explain_traceability(self) -> None:
        rec = _sample_recommendation()
        plan = CampaignPlanner().plan(rec)
        campaign = CampaignBuilder().build("easytech", rec, plan, origin_score=plan.origin_score)
        explain = build_campaign_explain(campaign=campaign, recommendation=rec, plan=plan)
        self.assertIn("rules_triggered", explain)
        self.assertIn("motor_reasoning", explain)
        self.assertEqual(explain["recommendation_id"], "rec_camp_test")


class CampaignEngineAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="camp_eng_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        self.tenant_root.mkdir(parents=True)
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"productos_servicios": ["EN1"]}),
            encoding="utf-8",
        )

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
            root.mkdir(parents=True, exist_ok=True)
            return {"content_queue": root / "content_queue.json", "campaigns": root / "campaigns.json"}

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", side_effect=lambda t: _paths(getattr(t, "tenant_id", t))),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.marketing_app.effective_app_paths", _app_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.default_app_id", return_value="default"),
            patch("Motor_Tecnico.accio_engine.marketing_app.normalize_app_id", side_effect=lambda x: x or "default"),
            patch("Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.effective_paths", side_effect=lambda t: _paths(t.tenant_id)),
            patch("Motor_Tecnico.accio_engine.knowledge_api.effective_paths", side_effect=lambda t: _paths(getattr(t, "tenant_id", t))),
            patch("Motor_Tecnico.accio_engine.knowledge_api.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch(
                "Motor_Tecnico.accio_engine.marketing_context_engine.builder.MarketingContextBuilder.build_for_recommendation",
                return_value={"company_brain": {"profile": {"productos_servicios": ["EN1"]}}},
            ),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@camp"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        self._seed_recommendation()

    def _reset(self) -> None:
        reset_campaign_use_cases()
        reset_decision_engine_use_cases()
        reset_brand_service()

    def _seed_recommendation(self) -> None:
        rec = _sample_recommendation()
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO recommendations (
                  tenant_id, recommendation_id, company_id, brand_id, title, description,
                  action, reason, expected_roi, priority, priority_score, owner_role, owner_id,
                  due_at, status, source, confidence, roadmap_id, justification_refs_json,
                  dependencies_json, created_by, approved_by, rejected_by, executed_at,
                  result_json, created_at, updated_at, explain_json, composed_json
                ) VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, NULL, ?, '[]',
                  ?, NULL, NULL, NULL, NULL, ?, ?, ?, ?
                )
                """,
                (
                    rec.tenant_id,
                    rec.recommendation_id,
                    rec.company_id,
                    rec.brand_id,
                    rec.title,
                    rec.description,
                    rec.action,
                    rec.reason,
                    rec.expected_roi,
                    rec.priority,
                    rec.priority_score,
                    rec.owner_role,
                    rec.status,
                    rec.source,
                    rec.confidence,
                    json.dumps(rec.justification_refs),
                    rec.created_by,
                    rec.created_at,
                    rec.updated_at,
                    json.dumps(rec.explain),
                    json.dumps(rec.composed),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self._reset()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_schema_v14(self) -> None:
        conn = get_connection()
        try:
            versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            conn.close()
        self.assertIn(14, versions)
        self.assertIn("campaign_channels", tables)
        self.assertIn("campaign_kpis", tables)
        self.assertIn("campaign_history", tables)

    def test_from_recommendation_and_explain(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/campaigns/from-recommendation/rec_camp_test",
            json={},
        )
        self.assertEqual(resp.status_code, 201, resp.get_data(as_text=True))
        body = resp.get_json()["data"]
        self.assertIn("campaign_id", body)
        self.assertEqual(body["recommendation_id"], "rec_camp_test")
        self.assertIn("explain", body)
        self.assertGreater(body.get("origin_score") or 0, 0)

        camp_id = body["campaign_id"]
        explain = self.client.get(f"/api/v1/tenants/{self.tenant_id}/campaigns/{camp_id}/explain")
        self.assertEqual(explain.status_code, 200)
        self.assertIn("explain", explain.get_json()["data"])

        enrich = self.client.post(f"/api/v1/tenants/{self.tenant_id}/campaigns/{camp_id}/enrich", json={})
        self.assertEqual(enrich.status_code, 200)
        enriched = enrich.get_json()["data"]
        self.assertTrue(enriched.get("llm_skipped"))

        approve = self.client.post(f"/api/v1/tenants/{self.tenant_id}/campaigns/{camp_id}/approve", json={})
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.get_json()["data"]["status"], "approved")


if __name__ == "__main__":
    unittest.main()
