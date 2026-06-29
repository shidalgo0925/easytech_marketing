#!/usr/bin/env python3
"""Tests Sprint 3 — M0 platform DB + M1 Corporate Memory."""

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
from Motor_Tecnico.accio_engine.marketing_plan_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.memory_api.routes import reset_use_cases_cache as reset_memory_cache  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


class PlatformMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="mem_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "memtenant"
        self.app_id = "default"
        tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        (tenant_root / "apps" / self.app_id / "marketing_plans").mkdir(parents=True)
        (tenant_root / "apps").joinpath("registry.json").write_text(
            json.dumps(
                {
                    "apps": [
                        {
                            "app_id": self.app_id,
                            "name": "Default",
                            "slug": self.app_id,
                            "status": "active",
                            "is_default": True,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id, "display_name": "Mem"}),
            encoding="utf-8",
        )

        reset_use_cases_cache()
        reset_memory_cache()
        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@mem"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch("Motor_Tecnico.accio_engine.marketing_plan_api.composition.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch(
                "Motor_Tecnico.accio_engine.marketing_plan_api.composition.resolve_tenant",
                return_value=type("T", (), {"tenant_id": self.tenant_id, "root": tenant_root})(),
            ),
            patch("Motor_Tecnico.accio_engine.marketing_plan_api.composition.marketing_app.get_app", return_value={"app_id": self.app_id}),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_memory_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)

    def test_m0_schema_created(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            conn.close()
        self.assertIn("memory_events", tables)

    def _plan_body(self, nombre: str = "Plan Mem") -> dict:
        return {
            "nombre": nombre,
            "objetivo_general": "Validar Corporate Memory",
            "strategy_type": "brand_awareness",
            "north_star_metric": "Leads",
            "success_criteria": ["10 leads"],
            "publico_objetivo": ["PYME"],
            "marketing_brief": "Brief test memory",
            "periodo": {"inicio": "2026-07-01", "fin": "2026-08-01"},
        }

    def test_plan_create_records_memory_event(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/apps/{self.app_id}/marketing-plans",
            json=self._plan_body(),
        )
        self.assertEqual(resp.status_code, 201, resp.get_data(as_text=True))

        mem = self.client.get(f"/api/v1/tenants/{self.tenant_id}/memory/events")
        self.assertEqual(mem.status_code, 200, mem.get_data(as_text=True))
        data = mem.get_json()["data"]
        self.assertGreaterEqual(len(data), 1)
        types = {row["event_type"] for row in data}
        self.assertIn("PlanCreated", types)
        self.assertEqual(data[0]["tenant_id"], self.tenant_id)

    def test_memory_event_detail(self) -> None:
        self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/apps/{self.app_id}/marketing-plans",
            json=self._plan_body("Plan Detail"),
        )
        listed = self.client.get(f"/api/v1/tenants/{self.tenant_id}/memory/events").get_json()["data"]
        event_id = listed[0]["event_id"]
        detail = self.client.get(f"/api/v1/tenants/{self.tenant_id}/memory/events/{event_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["data"]["event_id"], event_id)


if __name__ == "__main__":
    unittest.main()
