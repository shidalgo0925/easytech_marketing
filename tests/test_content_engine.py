#!/usr/bin/env python3
"""Tests Content Engine."""

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
from Motor_Tecnico.accio_engine.campaign_api.composition import reset_campaign_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_domain.model import Campaign, CampaignChannel  # noqa: E402
from Motor_Tecnico.accio_engine.content_engine_api.composition import reset_content_engine_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.content_engine_domain.content_builder import ContentBuilder  # noqa: E402
from Motor_Tecnico.accio_engine.content_engine_domain.content_explainability import build_content_explain  # noqa: E402
from Motor_Tecnico.accio_engine.content_engine_domain.content_planner import ContentPlanner  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _campaign() -> Campaign:
    now = datetime.now(timezone.utc).isoformat()
    return Campaign(
        tenant_id="easytech",
        campaign_id="cmp_test",
        brand_id="en1",
        name="Campaña EN1",
        channel="linkedin",
        status="approved",
        objective="Recuperar visibilidad",
        description="Marca inactiva",
        recommendation_id="rec_test",
        campaign_type="awareness",
        call_to_action="DIAGNÓSTICO",
        target_audience="B2B Panamá",
        value_proposition="Plataforma EN1",
        channels=(CampaignChannel("linkedin", "primary"),),
        origin_score=72.0,
        explain={"score": 72.0, "rules_triggered": [{"id": "brand_inactive"}]},
        created_at=now,
        updated_at=now,
    )


class ContentPlannerTests(unittest.TestCase):
    def test_plan(self) -> None:
        plan = ContentPlanner().plan(_campaign())
        self.assertEqual(len(plan.items), 1)
        self.assertEqual(plan.items[0].channel, "linkedin")


class ContentBuilderTests(unittest.TestCase):
    def test_build(self) -> None:
        camp = _campaign()
        plan = ContentPlanner().plan(camp)
        piece = ContentBuilder().build("easytech", camp, plan, plan.items[0])
        self.assertTrue(piece.content_id.startswith("cnt_"))
        self.assertEqual(piece.campaign_id, "cmp_test")


class ContentEngineAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="cnt_eng_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        ensure_schema()
        self._reset()
        self._seed_campaign()

        tenant_obj = type("T", (), {"tenant_id": "easytech", "root": Path(self.tmp)})()
        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch(
                "Motor_Tecnico.accio_engine.marketing_context_engine.builder.MarketingContextBuilder.build",
                return_value={"company_brain": {"profile": {}}},
            ),
        ]
        for p in self.patches:
            p.start()
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["role"] = "admin"
            sess["tenant_id"] = "easytech"

    def _reset(self) -> None:
        reset_content_engine_use_cases()
        reset_campaign_use_cases()
        reset_decision_engine_use_cases()

    def _seed_campaign(self) -> None:
        camp = _campaign()
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO campaigns (
                  tenant_id, campaign_id, brand_id, name, status, objective, channel,
                  payload_json, created_at, updated_at, recommendation_id, description,
                  target_audience, value_proposition, call_to_action, priority, owner,
                  campaign_type, frequency, channels_json, kpis_json, explain_json,
                  origin_score, llm_skipped
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)
                """,
                (
                    camp.tenant_id, camp.campaign_id, camp.brand_id, camp.name, camp.status,
                    camp.objective, camp.channel, "{}", camp.created_at, camp.updated_at,
                    camp.recommendation_id, camp.description, camp.target_audience,
                    camp.value_proposition, camp.call_to_action, "high", "marketing",
                    camp.campaign_type, "weekly", json.dumps([{"channel": "linkedin"}]),
                    "[]", json.dumps(camp.explain), camp.origin_score,
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

    def test_schema_v15(self) -> None:
        conn = get_connection()
        try:
            vers = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn(15, vers)
        self.assertIn("content_pieces", tables)

    def test_from_campaign_api(self) -> None:
        resp = self.client.post("/api/v1/tenants/easytech/content/from-campaign/cmp_test", json={})
        self.assertEqual(resp.status_code, 201, resp.get_data(as_text=True))
        body = resp.get_json()["data"]
        self.assertIn("content_id", body)
        self.assertEqual(body["campaign_id"], "cmp_test")
        self.assertIn("explain", body)

        explain = self.client.get(f"/api/v1/tenants/easytech/content/{body['content_id']}/explain")
        self.assertEqual(explain.status_code, 200)

        enrich = self.client.post(f"/api/v1/tenants/easytech/content/{body['content_id']}/enrich", json={})
        self.assertEqual(enrich.status_code, 200)
        self.assertTrue(enrich.get_json()["data"]["llm_skipped"])


if __name__ == "__main__":
    unittest.main()
