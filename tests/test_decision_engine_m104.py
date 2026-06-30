#!/usr/bin/env python3
"""Tests M10.4 — Daily Planner + roadmaps API."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.app import app  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _registry(apps: list[dict]) -> dict:
    return {
        "version": 1,
        "default_app_id": apps[0]["app_id"],
        "apps": apps,
    }


class DecisionEngineM104Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="de_m104_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "easytech"
        self.roadmap_date = "2026-06-26"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)

        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"productos_servicios": ["EasyNodeOne (EN1)"]}),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                _registry(
                    [
                        {"app_id": "default", "name": "EasyTech", "slug": "default", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "slug": "en1", "status": "active", "is_default": False},
                    ]
                )
            ),
            encoding="utf-8",
        )

        en1_queue = {
            "posts": [
                {
                    "id": "linkedin_11_en1_demo",
                    "platform": "linkedin",
                    "status": "pending",
                    "scheduled_at": "2026-07-24T13:00:00-05:00",
                    "content_type": "venta",
                    "text": "Post EN1",
                    "app_id": "en1",
                }
            ]
        }
        default_queue = {
            "posts": [
                {
                    "id": "linkedin_recent",
                    "platform": "linkedin",
                    "status": "published",
                    "published_at": "2026-06-20T10:00:00-05:00",
                    "text": "Reciente",
                    "app_id": "default",
                }
            ]
        }
        for app_id, queue in [("en1", en1_queue), ("default", default_queue)]:
            path = apps_dir / app_id / "content_queue.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(queue), encoding="utf-8")

        ensure_schema()
        reset_decision_engine()
        reset_use_cases_cache()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            return {"content_queue": root / "content_queue.json"}

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
            patch(
                "Motor_Tecnico.accio_engine.decision_engine_api.routes.tenant_today_iso",
                return_value=self.roadmap_date,
            ),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@roadmap"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_decision_engine()
        reset_use_cases_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_schema_v11_daily_roadmaps(self) -> None:
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
        finally:
            conn.close()
        self.assertIn("daily_roadmaps", tables)
        self.assertIn(11, versions)

    def test_generate_get_and_idempotent(self) -> None:
        gen = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/generate"
        )
        self.assertEqual(gen.status_code, 201, gen.get_data(as_text=True))
        body = gen.get_json()["data"]
        self.assertEqual(body["roadmap_date"], self.roadmap_date)
        self.assertGreaterEqual(body["summary"]["total"], 1)
        recs = body["recommendations"]
        self.assertTrue(all(r["roadmap_id"] == body["roadmap_id"] for r in recs))
        en1 = [r for r in recs if r["brand_id"] == "en1"]
        self.assertEqual(len(en1), 1)

        gen2 = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/generate"
        )
        self.assertEqual(gen2.status_code, 200, gen2.get_data(as_text=True))
        self.assertEqual(gen2.get_json()["data"]["roadmap_id"], body["roadmap_id"])

        get_resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(len(get_resp.get_json()["data"]["recommendations"]), len(recs))

        today = self.client.get(f"/api/v1/tenants/{self.tenant_id}/roadmaps/today")
        self.assertEqual(today.status_code, 200)
        self.assertEqual(today.get_json()["data"]["roadmap_id"], body["roadmap_id"])

    def test_daily_roadmap_generated_memory_event(self) -> None:
        self.client.post(f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/generate")
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT event_type FROM memory_events
                WHERE tenant_id = ? AND event_type = 'DailyRoadmapGenerated'
                ORDER BY timestamp DESC LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "DailyRoadmapGenerated")

    def test_get_missing_roadmap_returns_404(self) -> None:
        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/roadmaps/2099-01-01")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
