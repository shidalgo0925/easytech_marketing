#!/usr/bin/env python3
"""Tests Opportunity Engine F2 — promote to Decision Engine + dismiss."""

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
from Motor_Tecnico.accio_engine.brand_infrastructure.facade import reset_brand_service  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_infrastructure.facade import reset_campaign_service  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import reset_company_brain_service  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.routes import reset_use_cases_cache as reset_de_cache  # noqa: E402
from Motor_Tecnico.accio_engine.lead_infrastructure.facade import reset_lead_service  # noqa: E402
from Motor_Tecnico.accio_engine.opportunity_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402
from Motor_Tecnico.accio_engine.publication_infrastructure.facade import reset_publication_service  # noqa: E402


def _registry(apps: list[dict]) -> dict:
    return {
        "version": 1,
        "default_app_id": apps[0]["app_id"],
        "apps": apps,
    }


class OpportunityF2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="opp_f2_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_CAMPAIGN_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)

        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
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
                    "id": "linkedin_old_en1",
                    "platform": "linkedin",
                    "status": "published",
                    "published_at": "2026-05-01T10:00:00-05:00",
                    "text": "Post antiguo EN1",
                    "app_id": "en1",
                }
            ]
        }
        (apps_dir / "en1" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "en1" / "content_queue.json").write_text(json.dumps(en1_queue), encoding="utf-8")
        (apps_dir / "default" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "default" / "content_queue.json").write_text(
            json.dumps(
                {
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
            ),
            encoding="utf-8",
        )

        ensure_schema()
        self._reset_services()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            paths = {"content_queue": root / "content_queue.json"}
            if aid == "default":
                paths["campaigns"] = self.tenant_root / "campaigns.json"
            else:
                paths["campaigns"] = root / "campaigns.json"
            return paths

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
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@opp"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def _reset_services(self) -> None:
        reset_brand_service()
        reset_publication_service()
        reset_campaign_service()
        reset_company_brain_service()
        reset_lead_service()
        reset_decision_engine()
        reset_de_cache()
        reset_use_cases_cache()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self._reset_services()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_promote_creates_recommendation(self) -> None:
        detect = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        opp_id = detect.get_json()["data"]["opportunities"][0]["opportunity_id"]

        promote = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}/promote")
        self.assertEqual(promote.status_code, 201, promote.get_data(as_text=True))
        body = promote.get_json()["data"]
        self.assertEqual(body["opportunity"]["status"], "classified")
        self.assertIn("recommendation_id", body["opportunity"]["payload"])
        rec = body["recommendation"]
        self.assertEqual(rec["status"], "pending_approval")
        self.assertTrue(rec["source"].startswith("opportunity:"))

        promote2 = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}/promote")
        self.assertEqual(promote2.status_code, 409)

        conn = get_connection()
        try:
            rec_count = conn.execute(
                "SELECT COUNT(*) FROM recommendations WHERE tenant_id = ?",
                (self.tenant_id,),
            ).fetchone()[0]
            promoted_event = conn.execute(
                """
                SELECT event_type FROM memory_events
                WHERE tenant_id = ? AND event_type = 'OpportunityPromoted'
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(rec_count, 1)
        self.assertIsNotNone(promoted_event)

    def test_dismiss_opportunity(self) -> None:
        detect = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        opp_id = detect.get_json()["data"]["opportunities"][0]["opportunity_id"]

        dismiss = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}/dismiss")
        self.assertEqual(dismiss.status_code, 200)
        self.assertEqual(dismiss.get_json()["data"]["status"], "dismissed")

        promote = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}/promote")
        self.assertEqual(promote.status_code, 409)


if __name__ == "__main__":
    unittest.main()
