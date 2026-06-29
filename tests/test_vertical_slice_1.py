#!/usr/bin/env python3
"""Tests Vertical Slice 1 — API v1 marketing-plans + context + planner."""

from __future__ import annotations

import json
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


class VerticalSlice1ApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="vs1_")
        self.tenant_id = "vs1tenant"
        self.app_id = "default"
        tenant_root = Path(self.tmp) / self.tenant_id
        tenant_root.mkdir(parents=True)
        (tenant_root / "apps" / self.app_id / "marketing_plans").mkdir(parents=True)
        (tenant_root / "apps" / self.app_id / "knowledge").mkdir(parents=True)
        (tenant_root / "apps" / self.app_id).joinpath("profile.json").write_text(
            json.dumps({"tone": "profesional"}),
            encoding="utf-8",
        )
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
            json.dumps({"tenant_id": self.tenant_id, "display_name": "VS1"}),
            encoding="utf-8",
        )

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@vs1"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        self.access_patch = patch(
            "Motor_Tecnico.accio_engine.app._user_can_access_tenant",
            return_value=True,
        )
        self.perm_patch = patch(
            "Motor_Tecnico.accio_engine.app._check_request_permission",
            return_value=(True, None),
        )
        self.repo_root_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_plan_api.composition.TENANTS_ROOT",
            Path(self.tmp),
        )
        self.resolve_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_plan_api.composition.resolve_tenant",
            return_value=type("T", (), {"tenant_id": self.tenant_id, "root": tenant_root})(),
        )
        self.get_app_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_plan_api.composition.marketing_app.get_app",
            return_value=type(
                "App",
                (),
                {
                    "app_id": self.app_id,
                    "name": "Default",
                    "description": "",
                    "tone": "",
                    "target_audience": "",
                    "brand_colors": {},
                },
            )(),
        )
        self.bc_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_context_builder.knowledge_api.load_business_context",
            return_value={"company": "VS1 Co"},
        )
        self.paths_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_context_builder.marketing_app.effective_app_paths",
            return_value={
                "profile": tenant_root / "apps" / self.app_id / "profile.json",
                "knowledge_dir": tenant_root / "apps" / self.app_id / "knowledge",
            },
        )
        self.get_app_ctx_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_context_builder.marketing_app.get_app",
            return_value=type(
                "App",
                (),
                {
                    "app_id": self.app_id,
                    "name": "Default",
                    "description": "",
                    "tone": "",
                    "target_audience": "",
                    "brand_colors": {},
                },
            )(),
        )
        self.llm_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_planner.assistant_llm.llm_available",
            return_value=False,
        )
        for p in (
            self.repo_root_patch,
            self.resolve_patch,
            self.get_app_patch,
            self.bc_patch,
            self.paths_patch,
            self.llm_patch,
            self.get_app_ctx_patch,
            self.access_patch,
            self.perm_patch,
        ):
            p.start()
        reset_use_cases_cache()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))
        for p in (
            self.repo_root_patch,
            self.resolve_patch,
            self.get_app_patch,
            self.bc_patch,
            self.paths_patch,
            self.llm_patch,
            self.get_app_ctx_patch,
            self.access_patch,
            self.perm_patch,
        ):
            self.addCleanup(p.stop)
        self.addCleanup(reset_use_cases_cache)

    def _base(self) -> str:
        return f"/api/v1/tenants/{self.tenant_id}/apps/{self.app_id}"

    def test_create_activate_get_active_flow(self) -> None:
        create_body = {
            "nombre": "Plan VS1",
            "objetivo_general": "Validar slice vertical",
            "strategy_type": "lead_generation",
            "north_star_metric": "Leads",
            "success_criteria": ["10 leads"],
            "publico_objetivo": ["PYME"],
            "marketing_brief": "Brief de prueba",
            "periodo": {"inicio": "2026-07-01", "fin": "2026-09-30"},
            "budget": {"amount": "1000", "currency": "USD"},
            "prioridad": "alta",
        }
        r = self.client.post(
            f"{self._base()}/marketing-plans",
            json=create_body,
        )
        self.assertEqual(r.status_code, 201, r.get_data(as_text=True))
        plan = r.get_json()["data"]
        self.assertEqual(plan["estado"], "borrador")
        plan_id = plan["id"]

        r2 = self.client.get(f"{self._base()}/marketing-plans/{plan_id}")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["data"]["nombre"], "Plan VS1")

        r3 = self.client.post(f"{self._base()}/marketing-plans/{plan_id}/activate", json={})
        self.assertEqual(r3.status_code, 200, r3.get_data(as_text=True))
        self.assertEqual(r3.get_json()["data"]["estado"], "activo")

        r4 = self.client.get(f"{self._base()}/marketing-plans/active")
        self.assertEqual(r4.status_code, 200)
        active = r4.get_json()["data"]
        self.assertIsNotNone(active)
        self.assertEqual(active["id"], plan_id)

    def test_context_and_planner(self) -> None:
        create_body = {
            "nombre": "Plan Ctx",
            "objetivo_general": "Validar context builder y planner del slice vertical",
            "strategy_type": "brand_awareness",
            "north_star_metric": "Alcance orgánico mensual",
            "success_criteria": ["Alcance orgánico"],
            "publico_objetivo": ["PYME"],
            "marketing_brief": "Brief de prueba para context builder y planner del slice vertical",
            "periodo": {"inicio": "2026-07-01", "fin": "2026-08-01"},
            "budget": {"amount": "0", "currency": "USD"},
            "prioridad": "media",
        }
        r = self.client.post(f"{self._base()}/marketing-plans", json=create_body)
        plan_id = r.get_json()["data"]["id"]
        self.client.post(f"{self._base()}/marketing-plans/{plan_id}/activate", json={})

        ctx = self.client.get(f"{self._base()}/marketing-context")
        self.assertEqual(ctx.status_code, 200)
        body = ctx.get_json()["data"]
        self.assertIn("business_context", body)
        self.assertIn("marketing_plan_active", body)
        self.assertEqual(body["marketing_plan_active"]["id"], plan_id)

        prop = self.client.post(f"{self._base()}/planner/proposals", json={})
        self.assertEqual(prop.status_code, 200)
        proposals = prop.get_json()["data"]["proposals"]
        self.assertEqual(len(proposals), 3)


if __name__ == "__main__":
    unittest.main()
