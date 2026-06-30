#!/usr/bin/env python3
"""Tests Marketing Context Engine."""

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

from Motor_Tecnico.accio_engine.marketing_context_engine.builder import (  # noqa: E402
    MarketingContextBuilder,
    reset_marketing_context_builder,
)
from Motor_Tecnico.accio_engine.marketing_context_engine.constants import (  # noqa: E402
    COMMERCIAL_CTA,
    COMMERCIAL_GUIDE_URL,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema  # noqa: E402


class MarketingContextBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="mce_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"

        matrix_path = Path(self.tmp) / "Marketing" / "knowledge" / "sectors.json"
        matrix_path.parent.mkdir(parents=True)
        shutil.copy(BASE / "Marketing" / "knowledge" / "sectors.json", matrix_path)

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"empresa": "EasyTech", "productos_servicios": ["EN1"], "industria": "TI"}),
            encoding="utf-8",
        )
        (self.tenant_root / "editorial_rules.json").write_text(
            json.dumps({"interim_rule": "3 valor + 1 venta", "target_matrix": "95/5"}),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_app_id": "default",
                    "apps": [{"app_id": "default", "name": "EasyTech", "slug": "default", "status": "active", "is_default": True}],
                }
            ),
            encoding="utf-8",
        )
        (apps_dir / "default" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "default" / "content_queue.json").write_text(json.dumps({"posts": []}), encoding="utf-8")

        ensure_schema()
        reset_marketing_context_builder()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            return {"content_queue": root / "content_queue.json", "campaigns": root / "campaigns.json"}

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
            patch("Motor_Tecnico.accio_engine.knowledge_api.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.knowledge_api.effective_paths", side_effect=lambda t: _paths(t.tenant_id)),
            patch("Motor_Tecnico.accio_engine.knowledge_matrix_infrastructure.json_repository.BASE_DIR", Path(self.tmp)),
        ]
        for p in self.patches:
            p.start()
        self.builder = MarketingContextBuilder()

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_marketing_context_builder()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_minimal_context(self) -> None:
        ctx = self.builder.build(self.tenant_id)
        self.assertEqual(ctx["tenant_id"], self.tenant_id)
        self.assertIn("company_brain", ctx)
        self.assertIn("brands", ctx)
        self.assertIn("knowledge_matrix", ctx)
        self.assertEqual(ctx["commercial"]["cta"], COMMERCIAL_CTA)
        self.assertEqual(ctx["commercial"]["guide_url"], COMMERCIAL_GUIDE_URL)
        self.assertIn("3 valor", ctx["editorial"]["rule"])

    def test_build_for_llm_trimmed(self) -> None:
        ctx = self.builder.build_for_llm(self.tenant_id, purpose="enrich")
        self.assertEqual(ctx["purpose"], "enrich")
        self.assertIn("company", ctx)
        self.assertIn("commercial", ctx)


if __name__ == "__main__":
    unittest.main()
