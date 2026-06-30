#!/usr/bin/env python3
"""VS2 — Primera campaña publicada (dry-run E2E)."""

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
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _campaign() -> Campaign:
    now = datetime.now(timezone.utc).isoformat()
    return Campaign(
        tenant_id="easytech",
        campaign_id="cmp_vs2",
        brand_id="default",
        name="VS2 Campaña",
        channel="linkedin",
        status="approved",
        objective="Primera publicación",
        description="Vertical slice VS2",
        recommendation_id="rec_vs2",
        campaign_type="awareness",
        call_to_action="DIAGNÓSTICO",
        target_audience="B2B Panamá",
        value_proposition="EasyTech",
        channels=(CampaignChannel("linkedin", "primary"),),
        origin_score=80.0,
        explain={"score": 80.0},
        created_at=now,
        updated_at=now,
    )


class VS2ContentPublishTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="vs2_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        self.queue_dir = Path(self.tmp) / "Marketing" / "tenants" / "easytech" / "apps" / "default"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.queue_path = self.queue_dir / "content_queue.json"
        self.queue_path.write_text('{"posts": []}\n', encoding="utf-8")

        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_PUBLISH_ENABLED"] = "true"
        os.environ["ACCIO_LINKEDIN_PUBLISH_ENABLED"] = "true"
        os.environ["ACCIO_PUBLISH_DRY_RUN"] = "false"

        ensure_schema()
        self._reset()
        self._seed_campaign()

        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch(
                "Motor_Tecnico.accio_engine.marketing_context_engine.builder.MarketingContextBuilder.build",
                return_value={"company_brain": {"profile": {}}},
            ),
            patch(
                "Motor_Tecnico.accio_engine.marketing_app.queue_file_path",
                return_value=self.queue_path,
            ),
            patch(
                "Motor_Tecnico.accio_engine.executor.load_content_queue",
                side_effect=self._load_queue,
            ),
            patch(
                "Motor_Tecnico.accio_engine.executor.save_content_queue",
                side_effect=self._save_queue,
            ),
        ]
        for p in self.patches:
            p.start()
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["role"] = "admin"
            sess["tenant_id"] = "easytech"
            sess["user_id"] = "test_user"

    def _load_queue(self, tenant_id: str, app_id=None) -> dict:
        return json.loads(self.queue_path.read_text(encoding="utf-8"))

    def _save_queue(self, data, tenant_id: str, app_id=None) -> None:
        self.queue_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

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
        for key in ("ACCIO_PLATFORM_DB", "ACCIO_PUBLISH_ENABLED", "ACCIO_LINKEDIN_PUBLISH_ENABLED", "ACCIO_PUBLISH_DRY_RUN"):
            os.environ.pop(key, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_schema_v16(self) -> None:
        conn = get_connection()
        try:
            vers = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
            cols = {r[1] for r in conn.execute("PRAGMA table_info(content_pieces)").fetchall()}
        finally:
            conn.close()
        self.assertIn(16, vers)
        self.assertIn("approved_by", cols)
        self.assertIn("publish_result_json", cols)

    def test_vs2_end_to_end_dry_run(self) -> None:
        create = self.client.post("/api/v1/tenants/easytech/content/from-campaign/cmp_vs2", json={})
        self.assertEqual(create.status_code, 201, create.get_data(as_text=True))
        cid = create.get_json()["data"]["content_id"]

        approve = self.client.post(f"/api/v1/tenants/easytech/content/{cid}/approve", json={})
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.get_json()["data"]["status"], "approved")

        queue = self.client.post(f"/api/v1/tenants/easytech/content/{cid}/queue", json={})
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(queue.get_json()["data"]["status"], "queued")

        queue_data = json.loads(self.queue_path.read_text(encoding="utf-8"))
        self.assertEqual(len(queue_data["posts"]), 1)
        self.assertEqual(queue_data["posts"][0]["id"], cid)

        publish = self.client.post(
            f"/api/v1/tenants/easytech/content/{cid}/publish-now",
            json={"dry_run": True},
        )
        self.assertEqual(publish.status_code, 200, publish.get_data(as_text=True))
        body = publish.get_json()["data"]
        self.assertTrue(body["dry_run"])
        self.assertEqual(body["status"], "published")
        self.assertTrue(body["external_post_id"].startswith("dry_"))

        history = self.client.get(f"/api/v1/tenants/easytech/content/{cid}/history")
        self.assertEqual(history.status_code, 200)
        events = [h["event_type"] for h in history.get_json()["data"]]
        self.assertIn("approved", events)
        self.assertIn("queued", events)
        self.assertIn("published", events)

        pub_queue = self.client.get("/api/v1/tenants/easytech/content/queue")
        self.assertEqual(pub_queue.status_code, 200)
        ids = [r["content_id"] for r in pub_queue.get_json()["data"]]
        self.assertIn(cid, ids)


if __name__ == "__main__":
    unittest.main()
