#!/usr/bin/env python3
"""Tests Asistente IA V1 — env, contexto, órdenes y auditoría."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import assistant_llm, assistant_service, assistant_store  # noqa: E402


class AssistantV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.tenant_dir = self.root / "easytech"
        self.tenant_dir.mkdir(parents=True)
        (self.root / "registry.json").write_text(
            json.dumps({"version": 2, "tenants": [{"tenant_id": "easytech", "display_name": "ET", "status": "active"}]}),
            encoding="utf-8",
        )
        apps = self.tenant_dir / "apps"
        apps.mkdir(parents=True)
        (apps / "default").mkdir(parents=True)
        (apps / "registry.json").write_text(
            json.dumps(
                {
                    "default_app_id": "default",
                    "apps": [
                        {"app_id": "default", "name": "ET", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "status": "active", "is_default": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        (apps / "en1").mkdir(parents=True)
        (apps / "en1" / "profile.json").write_text(
            json.dumps({"app_id": "en1", "name": "EN1", "tone": "Técnico", "target_audience": "PYME"}),
            encoding="utf-8",
        )
        (apps / "en1" / "content_queue.json").write_text(json.dumps({"posts": []}), encoding="utf-8")
        (apps / "default" / "content_queue.json").write_text(
            json.dumps({"posts": [{"id": "p1", "platform": "linkedin", "status": "draft", "text": "Test", "app_id": "default"}]}),
            encoding="utf-8",
        )
        (self.tenant_dir / "products.json").write_text(
            json.dumps({"products": [{"slug": "en1", "name": "EN1", "cta": "DEMO"}]}),
            encoding="utf-8",
        )
        (self.tenant_dir / "ai.json").write_text(
            json.dumps({"topic_model": "llm", "enabled": True}),
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch(self):
        return mock.patch.multiple(
            "Motor_Tecnico.accio_engine.tenant",
            TENANTS_ROOT=self.root,
            REGISTRY_PATH=self.root / "registry.json",
        )

    def test_llm_available_requires_openai_key(self):
        with mock.patch.dict(os.environ, {"AI_ASSISTANT_ENABLED": "true"}, clear=False):
            with mock.patch.object(assistant_llm, "resolve_openai_key", return_value=""):
                self.assertFalse(assistant_llm.llm_available("easytech", {"enabled": True}))

    def test_assistant_disabled_via_env(self):
        with mock.patch.dict(os.environ, {"AI_ASSISTANT_ENABLED": "false"}, clear=False):
            with mock.patch.object(assistant_llm, "resolve_openai_key", return_value="sk-test"):
                self.assertFalse(assistant_llm.llm_available("easytech", {"enabled": True}))

    def test_resolve_model_from_env(self):
        with mock.patch.dict(os.environ, {"OPENAI_MODEL": "gpt-4o"}, clear=False):
            self.assertEqual(assistant_llm.resolve_model("easytech"), "gpt-4o")

    def test_build_context_includes_products_and_connectors(self):
        with self._patch():
            with mock.patch.object(assistant_service, "_connectors_summary", return_value=[{"id": "linkedin", "active": True}]):
                ctx = assistant_service.build_context("easytech", "default")
        self.assertEqual(ctx["tenant_id"], "easytech")
        self.assertEqual(ctx["app_id"], "default")
        self.assertTrue(ctx["products"])
        self.assertEqual(ctx["connectors"][0]["id"], "linkedin")

    def test_apps_catalog_includes_all_apps(self):
        with self._patch():
            catalog = assistant_service.build_apps_catalog("easytech", "default")
        app_ids = {a["app_id"] for a in catalog}
        self.assertIn("default", app_ids)
        self.assertIn("en1", app_ids)
        en1 = next(a for a in catalog if a["app_id"] == "en1")
        self.assertEqual(en1["tone"], "Técnico")
        self.assertFalse(en1["selected_now"])
        default = next(a for a in catalog if a["app_id"] == "default")
        self.assertTrue(default["selected_now"])

    def test_order_starts_pending_approval(self):
        with self._patch():
            order = assistant_store.create_order(
                "easytech",
                app_id="default",
                action_type="create_posts",
                title="Test",
                preview=[{"id": "x1", "status": "pending_approval"}],
            )
        self.assertEqual(order["status"], "pending_approval")

    def test_audit_record(self):
        with self._patch():
            entry = assistant_store.record_audit(
                "easytech",
                user="tester",
                app_id="default",
                prompt="Hola",
                response="Respuesta",
                model="gpt-4o-mini",
            )
            history = assistant_store.list_audit("easytech", limit=5)
        self.assertEqual(entry["user"], "tester")
        self.assertEqual(history[0]["prompt"], "Hola")

    def test_missing_key_returns_error_code(self):
        with self._patch():
            with mock.patch.object(assistant_llm, "resolve_openai_key", return_value=""):
                result = assistant_service.process_message("easytech", "Hola", app_id="default")
        self.assertTrue(result["ok"])
        self.assertFalse(result["llm"])
        self.assertEqual(result.get("error_code"), "OPENAI_KEY_MISSING")


if __name__ == "__main__":
    unittest.main()
