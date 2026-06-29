#!/usr/bin/env python3
"""Tests publicaciones e asistente IA."""

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

from Motor_Tecnico.accio_engine import assistant_service, publications_api  # noqa: E402


class PublicationsAssistantTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.tenant_dir = self.root / "easytech"
        self.tenant_dir.mkdir(parents=True)
        (self.root / "registry.json").write_text(
            json.dumps({"version": 2, "tenants": [{"tenant_id": "easytech", "display_name": "ET", "status": "active"}]}),
            encoding="utf-8",
        )
        (self.tenant_dir / "apps").mkdir(parents=True)
        (self.tenant_dir / "apps" / "registry.json").write_text(
            json.dumps(
                {
                    "default_app_id": "default",
                    "apps": [{"app_id": "default", "name": "ET", "status": "active", "is_default": True}],
                }
            ),
            encoding="utf-8",
        )
        (self.tenant_dir / "content_queue.json").write_text(
            json.dumps(
                {
                    "posts": [
                        {
                            "id": "p1",
                            "platform": "linkedin",
                            "status": "published",
                            "scheduled_at": "2026-07-01T13:00:00-05:00",
                            "published_at": "2026-07-02T13:00:00-05:00",
                            "text": "Hola",
                            "app_id": "default",
                        },
                        {
                            "id": "p2",
                            "platform": "linkedin",
                            "status": "draft",
                            "scheduled_at": "2026-07-03T13:00:00-05:00",
                            "text": "Borrador",
                            "app_id": "default",
                        },
                    ]
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

    def test_list_publications(self):
        with self._patch():
            data = publications_api.list_publications("easytech")
            self.assertEqual(data["total"], 2)
            statuses = {p["status"] for p in data["publications"]}
            self.assertIn("published", statuses)
            self.assertIn("draft", statuses)

    def test_assistant_queue_review(self):
        with self._patch():
            result = assistant_service.process_message("easytech", "Revisa la cola y dime qué está débil", app_id="default")
            self.assertTrue(result["ok"])
            self.assertIn("Cola", result["response"])


if __name__ == "__main__":
    unittest.main()
