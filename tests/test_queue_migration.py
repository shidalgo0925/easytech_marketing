#!/usr/bin/env python3
"""Tests de migración cola default → apps."""

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

from Motor_Tecnico.accio_engine import marketing_app, queue_migration  # noqa: E402


class QueueMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.tenant_dir = self.root / "easytech"
        self.tenant_dir.mkdir(parents=True)
        (self.root / "registry.json").write_text(
            json.dumps(
                {
                    "version": 2,
                    "tenants": [{"tenant_id": "easytech", "display_name": "EasyTech", "status": "active"}],
                }
            ),
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

    def _setup_tenant(self):
        apps_reg = self.tenant_dir / "apps" / "registry.json"
        apps_reg.parent.mkdir(parents=True, exist_ok=True)
        apps_reg.write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_app_id": "default",
                    "apps": [
                        {"app_id": "default", "name": "EasyTech", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "status": "active", "is_default": False},
                        {"app_id": "odoo-fe", "name": "Odoo FE", "status": "active", "is_default": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.tenant_dir / "content_queue.json").write_text(
            json.dumps(
                {
                    "posts": [
                        {"id": "p_en1", "platform": "linkedin", "status": "pending", "flyer_num": 5, "scheduled_at": "2026-07-01T13:00:00-05:00"},
                        {"id": "p_diag", "platform": "linkedin", "status": "pending", "flyer_num": 11, "scheduled_at": "2026-07-02T13:00:00-05:00"},
                        {"id": "p_odoo", "platform": "linkedin", "status": "pending", "flyer_num": 3, "scheduled_at": "2026-07-03T13:00:00-05:00"},
                    ]
                }
            ),
            encoding="utf-8",
        )

    def test_resolve_app_for_post(self):
        with self._patch():
            self._setup_tenant()
            self.assertEqual(queue_migration.resolve_app_for_post({"flyer_num": 5}, "easytech"), "en1")
            self.assertEqual(queue_migration.resolve_app_for_post({"flyer_num": 11}, "easytech"), "default")
            self.assertEqual(queue_migration.resolve_app_for_post({"flyer_num": 3}, "easytech"), "odoo-fe")

    def test_migrate_moves_product_posts(self):
        with self._patch():
            self._setup_tenant()
            marketing_app.provision_app_directory("easytech", "en1")
            marketing_app.provision_app_directory("easytech", "odoo-fe")
            result = queue_migration.migrate_default_queue_to_apps("easytech", backup=False)
            self.assertEqual(result["moved"], 2)
            self.assertEqual(result["kept_default"], 1)
            default_q = json.loads((self.tenant_dir / "content_queue.json").read_text())
            self.assertEqual([p["id"] for p in default_q["posts"]], ["p_diag"])
            en1_q = json.loads((self.tenant_dir / "apps" / "en1" / "content_queue.json").read_text())
            self.assertEqual(len(en1_q["posts"]), 1)
            self.assertEqual(en1_q["posts"][0]["app_id"], "en1")


if __name__ == "__main__":
    unittest.main()
