#!/usr/bin/env python3
"""Tests M2 — Company Brain."""

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
from Motor_Tecnico.accio_engine.company_brain_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_infrastructure.facade import reset_company_brain_service  # noqa: E402
from Motor_Tecnico.accio_engine.memory_api.routes import reset_use_cases_cache as reset_memory_cache  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


class CompanyBrainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="brain_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "braintenant"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        self.tenant_root.mkdir(parents=True)
        legacy = {
            "version": 1,
            "empresa": "Test Co",
            "industria": "TI",
            "pais": "Panamá",
        }
        (self.tenant_root / "business_context.json").write_text(
            json.dumps(legacy, ensure_ascii=False),
            encoding="utf-8",
        )
        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )

        reset_use_cases_cache()
        reset_company_brain_service()
        reset_memory_cache()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@brain"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", side_effect=lambda t: _paths(t.tenant_id)),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.resolve_tenant",
                return_value=tenant_obj,
            ),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.effective_paths",
                side_effect=lambda t: _paths(t.tenant_id),
            ),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_company_brain_service()
        reset_memory_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_BRAIN_STORE", None)

    def test_schema_v2_company_profiles(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("company_profiles", tables)

    def test_get_company_brain_from_legacy(self) -> None:
        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/company-brain")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(data["profile"]["empresa"], "Test Co")

    def test_patch_writes_sql_and_json(self) -> None:
        resp = self.client.patch(
            f"/api/v1/tenants/{self.tenant_id}/company-brain",
            json={"cta_principal": "DIAGNÓSTICO"},
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))

        legacy = json.loads((self.tenant_root / "business_context.json").read_text(encoding="utf-8"))
        self.assertEqual(legacy["cta_principal"], "DIAGNÓSTICO")

        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT profile_json FROM company_profiles WHERE tenant_id = ?",
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertIn("DIAGNÓSTICO", row[0])

        mem = self.client.get(f"/api/v1/tenants/{self.tenant_id}/memory/events?event_type=CompanyBrainUpdated")
        events = mem.get_json()["data"]
        self.assertGreaterEqual(len(events), 1)


if __name__ == "__main__":
    unittest.main()
