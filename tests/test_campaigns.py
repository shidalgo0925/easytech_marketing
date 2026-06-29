#!/usr/bin/env python3
"""Tests M7 — Campaigns."""

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
from Motor_Tecnico.accio_engine import dashboard_data  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.campaign_infrastructure.facade import reset_campaign_service  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


SAMPLE_CAMPAIGNS = {
    "updated_at": "2026-06-20",
    "campaigns": [
        {
            "id": "camp_en1",
            "post_id": "linkedin_11_en1_demo",
            "product": "EN1 / EasyNodeOne",
            "flyer_num": 5,
            "content_type": "venta",
            "landing": "https://n8n.etsrv.site/guia/",
            "cta": "EN1",
        }
    ],
}


class CampaignsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="camp_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_CAMPAIGN_STORE"] = "dual"

        self.tenant_id = "easytech"
        self.app_id = "default"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        self.tenant_root.mkdir(parents=True)
        (self.tenant_root / "campaigns.json").write_text(json.dumps(SAMPLE_CAMPAIGNS), encoding="utf-8")
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "content_queue.json").write_text(
            json.dumps(
                {
                    "posts": [
                        {
                            "id": "linkedin_11_en1_demo",
                            "platform": "linkedin",
                            "status": "scheduled",
                            "scheduled_at": "2026-07-01T10:00:00-05:00",
                            "text": "Post EN1",
                            "app_id": "default",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        flyers_manifest = self.tenant_root / "flyers" / "manifest.json"
        flyers_manifest.parent.mkdir(parents=True, exist_ok=True)
        flyers_manifest.write_text(json.dumps({"flyers": [{"num": 5, "topic": "EN1"}]}), encoding="utf-8")

        reset_use_cases_cache()
        reset_campaign_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _effective_paths(tid, app_id=None):
            from Motor_Tecnico.accio_engine import marketing_app

            aid = marketing_app.normalize_app_id(app_id) if app_id else marketing_app.default_app_id(tid)
            if aid == marketing_app.default_app_id(tid):
                return {
                    "campaigns": self.tenant_root / "campaigns.json",
                    "content_queue": self.tenant_root / "content_queue.json",
                    "calendar": self.tenant_root / "calendar.json",
                    "flyers_manifest": self.tenant_root / "flyers" / "manifest.json",
                    "knowledge_dir": self.tenant_root / "knowledge",
                    "knowledge_manifest": self.tenant_root / "knowledge" / "manifest.json",
                }
            root = self.tenant_root / "apps" / aid
            return {
                "campaigns": root / "campaigns.json",
                "content_queue": root / "content_queue.json",
                "calendar": root / "calendar.json",
                "flyers_manifest": self.tenant_root / "flyers" / "manifest.json",
                "knowledge_dir": self.tenant_root / "knowledge",
                "knowledge_manifest": self.tenant_root / "knowledge" / "manifest.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid if aid != "default" else self.tenant_root
            return {
                "content_queue": (root / "content_queue.json") if aid != "default" else self.tenant_root / "content_queue.json",
                "campaigns": (root / "campaigns.json") if aid != "default" else self.tenant_root / "campaigns.json",
            }

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.dashboard_data.effective_paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.dashboard_data._paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.marketing_app.effective_app_paths", _app_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.default_app_id", return_value="default"),
            patch("Motor_Tecnico.accio_engine.marketing_app.normalize_app_id", side_effect=lambda x: x or "default"),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
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

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_campaign_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_CAMPAIGN_STORE", None)

    def test_schema_v7_campaigns(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("campaigns", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.campaign_infrastructure.legacy_mapper import store_to_campaigns
        from Motor_Tecnico.accio_engine.campaign_infrastructure.sqlite_repository import SqliteCampaignRepository

        campaigns = store_to_campaigns(self.tenant_id, self.app_id, SAMPLE_CAMPAIGNS)
        SqliteCampaignRepository().save_all_for_brand(self.tenant_id, self.app_id, campaigns)
        reset_campaign_service()
        reset_use_cases_cache()
        os.environ["ACCIO_CAMPAIGN_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/apps/{self.app_id}/campaigns")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["campaign_id"], "camp_en1")

    def test_dashboard_data_delegates_to_sql(self) -> None:
        from Motor_Tecnico.accio_engine.campaign_infrastructure.legacy_mapper import store_to_campaigns
        from Motor_Tecnico.accio_engine.campaign_infrastructure.sqlite_repository import SqliteCampaignRepository

        campaigns = store_to_campaigns(self.tenant_id, self.app_id, SAMPLE_CAMPAIGNS)
        SqliteCampaignRepository().save_all_for_brand(self.tenant_id, self.app_id, campaigns)
        reset_campaign_service()
        os.environ["ACCIO_CAMPAIGN_STORE"] = "sql"

        rows = dashboard_data.load_campaigns(self.tenant_id, self.app_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "camp_en1")
        self.assertEqual(rows[0]["product"], "EN1 / EasyNodeOne")


if __name__ == "__main__":
    unittest.main()
