#!/usr/bin/env python3
"""Tests del modelo App (marketing) dentro de tenant."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import marketing_app  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_app import AppNotFoundError, DEFAULT_APP_ID  # noqa: E402


class MarketingAppTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.tenant_dir = self.root / "easytech"
        self.tenant_dir.mkdir(parents=True)
        registry = self.root / "registry.json"
        registry.write_text(
            json.dumps(
                {
                    "version": 2,
                    "tenants": [
                        {
                            "tenant_id": "easytech",
                            "display_name": "Easy Technology Services",
                            "status": "active",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.tenant_dir / "products.json").write_text(
            json.dumps(
                {
                    "products": [
                        {"slug": "easynodeone_en1_plataforma_todo_en_uno", "name": "Easy NodeOne", "enabled": True},
                        {"slug": "epayroll_planilla_panam", "name": "EPayRoll", "enabled": True},
                    ]
                }
            ),
            encoding="utf-8",
        )
        (self.tenant_dir / "content_queue.json").write_text(
            json.dumps({"posts": [{"id": "p1", "status": "pending", "platform": "linkedin"}]}),
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

    def test_bootstrap_creates_default_and_product_apps(self):
        with self._patch():
            reg = marketing_app.bootstrap_registry("easytech")
            ids = {a["app_id"] for a in reg["apps"]}
            self.assertIn(DEFAULT_APP_ID, ids)
            self.assertIn("en1", ids)
            self.assertIn("epayroll", ids)
            self.assertEqual(reg["default_app_id"], DEFAULT_APP_ID)

    def test_default_app_uses_tenant_root_paths(self):
        with self._patch():
            marketing_app.bootstrap_registry("easytech")
            paths = marketing_app.effective_app_paths("easytech", DEFAULT_APP_ID)
            self.assertTrue(paths["content_queue"].samefile(self.tenant_dir / "content_queue.json"))

    def test_create_app_scoped_paths(self):
        with self._patch():
            marketing_app.bootstrap_registry("easytech")
            app = marketing_app.create_app("easytech", {"app_id": "modecosa-line", "name": "Línea test"})
            paths = marketing_app.effective_app_paths("easytech", app.app_id)
            self.assertEqual(paths["app_root"], self.tenant_dir / "apps" / "modecosa-line")
            self.assertTrue(paths["content_queue"].is_file())

    def test_ensure_post_app_ids(self):
        with self._patch():
            marketing_app.bootstrap_registry("easytech")
            n = marketing_app.ensure_post_app_ids("easytech")
            self.assertEqual(n, 1)
            data = json.loads((self.tenant_dir / "content_queue.json").read_text())
            self.assertEqual(data["posts"][0]["app_id"], DEFAULT_APP_ID)

    def test_unknown_app_raises(self):
        with self._patch():
            marketing_app.bootstrap_registry("easytech")
            with self.assertRaises(AppNotFoundError):
                marketing_app.get_app("easytech", "no-existe")

    def test_provision_app_directory(self):
        with self._patch():
            marketing_app.bootstrap_registry("easytech")
            marketing_app.create_app("easytech", {"app_id": "en1-test", "name": "EN1 Test"})
            paths = marketing_app.provision_app_directory("easytech", "en1-test")
            self.assertTrue((paths["app_root"] / "profile.json").is_file())
            self.assertTrue((paths["app_root"] / "content_queue.json").is_file())
            self.assertTrue((paths["app_root"] / "knowledge").is_dir())
            self.assertTrue((paths["app_root"] / "metrics").is_dir())


if __name__ == "__main__":
    unittest.main()
