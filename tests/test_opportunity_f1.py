#!/usr/bin/env python3
"""Tests Opportunity Engine F1 — detect, list, memory."""

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


class OpportunityF1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="opp_f1_")
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

        (self.tenant_root / "campaigns.json").write_text(
            json.dumps(
                {
                    "campaigns": [
                        {
                            "id": "camp_stalled_1",
                            "name": "Campaña Q2 pausada",
                            "product": "EasyTech",
                            "channel": "linkedin",
                            "status": "paused",
                            "updated_at": "2026-05-01T10:00:00-05:00",
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
        reset_use_cases_cache()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        self._reset_services()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_schema_v12_opportunities(self) -> None:
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
        finally:
            conn.close()
        self.assertIn("opportunities", tables)
        self.assertIn(12, versions)

    def test_detect_list_and_idempotent(self) -> None:
        detect = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        self.assertEqual(detect.status_code, 201, detect.get_data(as_text=True))
        body = detect.get_json()["data"]
        self.assertGreaterEqual(body["created_count"], 1)
        opps = body["opportunities"]
        signal_types = {o["signal_type"] for o in opps}
        self.assertIn("brand_inactive", signal_types)
        en1 = next(o for o in opps if o["brand_id"] == "en1")
        self.assertEqual(en1["sector"], "Servicios B2B")
        self.assertEqual(en1["product_slug"], "en1")
        self.assertIn("matrix", en1["payload"])

        detect2 = self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        self.assertEqual(detect2.status_code, 200)
        self.assertEqual(detect2.get_json()["data"]["created_count"], 0)
        self.assertGreaterEqual(detect2.get_json()["data"]["updated_count"], 1)

        listing = self.client.get(f"/api/v1/tenants/{self.tenant_id}/opportunities")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(len(listing.get_json()["data"]), 1)

        opp_id = opps[0]["opportunity_id"]
        one = self.client.get(f"/api/v1/tenants/{self.tenant_id}/opportunities/{opp_id}")
        self.assertEqual(one.status_code, 200)
        self.assertEqual(one.get_json()["data"]["opportunity_id"], opp_id)

    def test_detect_memory_event(self) -> None:
        self.client.post(f"/api/v1/tenants/{self.tenant_id}/opportunities/detect")
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT event_type FROM memory_events
                WHERE tenant_id = ? AND event_type = 'OpportunityIdentified'
                ORDER BY timestamp DESC LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "OpportunityIdentified")


if __name__ == "__main__":
    unittest.main()
