#!/usr/bin/env python3
"""Tests de aislamiento multi-tenant (Fase B V2)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import executor, knowledge_api, tenant_profile  # noqa: E402
from Motor_Tecnico.accio_engine.tenant import DEFAULT_TENANT, list_tenants, resolve_tenant  # noqa: E402


class TenantIsolationTests(unittest.TestCase):
    def test_registry_has_easytech_and_relatic(self):
        ids = {t.tenant_id for t in list_tenants()}
        self.assertIn("easytech", ids)
        self.assertIn("relatic", ids)

    def test_content_queue_not_shared(self):
        easy = executor.load_content_queue("easytech")
        rel = executor.load_content_queue("relatic")
        easy_count = len(easy.get("posts", []))
        rel_count = len(rel.get("posts", []))
        self.assertGreater(easy_count, 0, "easytech debe tener posts")
        self.assertEqual(rel_count, 0, "relatic debe tener cola vacía")

    def test_knowledge_not_shared(self):
        easy_kb = knowledge_api.list_knowledge("easytech")
        rel_kb = knowledge_api.list_knowledge("relatic")
        self.assertGreater(len(easy_kb), 0)
        self.assertEqual(len(rel_kb), 0)

    def test_tenant_paths_distinct(self):
        e = resolve_tenant("easytech")
        r = resolve_tenant("relatic")
        self.assertNotEqual(e.root, r.root)
        self.assertTrue(str(e.root).endswith("/easytech"))
        self.assertTrue(str(r.root).endswith("/relatic"))

    def test_branding_profiles_exist(self):
        for tid in ("easytech", "relatic"):
            profile = tenant_profile.load_profile(tid)
            self.assertEqual(profile["tenant_id"], tid)
            self.assertIn("branding", profile)
            self.assertRegex(profile["branding"]["primary_color"], r"^#[0-9A-Fa-f]{6}$")

    def test_invalid_tenant_raises(self):
        with self.assertRaises(Exception):
            resolve_tenant("no_existe_xyz")


if __name__ == "__main__":
    unittest.main()
