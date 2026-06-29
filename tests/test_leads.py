#!/usr/bin/env python3
"""Tests M9 — Leads."""

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
from Motor_Tecnico.accio_engine import leads_store  # noqa: E402
from Motor_Tecnico.accio_engine.lead_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.lead_infrastructure.facade import reset_lead_service  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


SAMPLE_LEADS = {
    "version": 1,
    "leads": [
        {
            "id": "lead_abc123",
            "tenant_id": "easytech",
            "app_id": "en1",
            "source": "landing",
            "channel": "web",
            "status": "new",
            "contact": {"email": "test@example.com"},
            "created_at": "2026-06-20T10:00:00+00:00",
        }
    ],
}


class LeadsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="lead_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_LEAD_STORE"] = "dual"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        self.tenant_root.mkdir(parents=True)
        (self.tenant_root / "leads.json").write_text(json.dumps(SAMPLE_LEADS), encoding="utf-8")
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")

        reset_use_cases_cache()
        reset_lead_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.leads_store.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.lead_infrastructure.json_repository.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@lead"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_lead_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_LEAD_STORE", None)

    def test_schema_v9_leads(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("leads", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.lead_infrastructure.legacy_mapper import catalog_to_leads
        from Motor_Tecnico.accio_engine.lead_infrastructure.sqlite_repository import SqliteLeadRepository

        leads = catalog_to_leads(self.tenant_id, SAMPLE_LEADS)
        SqliteLeadRepository().save_all_for_tenant(self.tenant_id, leads)
        reset_lead_service()
        reset_use_cases_cache()
        os.environ["ACCIO_LEAD_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/leads")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "lead_abc123")

    def test_record_lead_delegates_to_sql(self) -> None:
        reset_lead_service()
        os.environ["ACCIO_LEAD_STORE"] = "sql"

        entry = leads_store.record_lead(
            self.tenant_id,
            app_id="en1",
            source="api_test",
            contact={"email": "new@example.com"},
        )
        self.assertTrue(entry["id"].startswith("lead_"))

        items = leads_store.list_leads(self.tenant_id)
        self.assertGreaterEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
