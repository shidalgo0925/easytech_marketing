#!/usr/bin/env python3
"""Tests sync read-only EN1 organizations ↔ tenant_id."""

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

from Motor_Tecnico.accio_engine import en1_organizations  # noqa: E402


class En1OrganizationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.sync_dir = self.root / ".en1"
        self.sync_dir.mkdir(parents=True)
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
                            "crm_target": "odoo",
                        },
                        {
                            "tenant_id": "relatic",
                            "display_name": "Relatic",
                            "status": "active",
                            "crm_target": "en1",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        ref_path = self.sync_dir / "reference_organizations.json"
        ref_path.write_text(
            json.dumps({"organizations": en1_organizations.REFERENCE_ORGANIZATIONS}),
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch(self):
        return (
            mock.patch.multiple(
                "Motor_Tecnico.accio_engine.tenant",
                TENANTS_ROOT=self.root,
                REGISTRY_PATH=self.root / "registry.json",
            ),
            mock.patch.multiple(
                "Motor_Tecnico.accio_engine.en1_organizations",
                SYNC_DIR=self.sync_dir,
                REFERENCE_PATH=self.sync_dir / "reference_organizations.json",
                CACHE_PATH=self.sync_dir / "organizations_cache.json",
            ),
        )

    def test_fetch_reference_when_api_missing(self):
        p1, p2 = self._patch()
        with p1, p2:
            with mock.patch.dict("os.environ", {}, clear=True):
                result = en1_organizations.fetch_organizations(allow_reference=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "reference")
        self.assertGreaterEqual(len(result["organizations"]), 4)

    def test_sync_suggests_relatic_mapping(self):
        p1, p2 = self._patch()
        with p1, p2:
            with mock.patch.dict("os.environ", {}, clear=True):
                report = en1_organizations.build_sync_report()
        relatic_suggestions = [s for s in report["suggestions"] if s["tenant_id"] == "relatic"]
        self.assertTrue(relatic_suggestions)
        self.assertEqual(relatic_suggestions[0]["suggested_en1_organization_id"], 3)

    def test_set_tenant_mapping_updates_registry(self):
        p1, p2 = self._patch()
        with p1, p2:
            mapping = en1_organizations.set_tenant_mapping("relatic", en1_organization_id=3)
        self.assertEqual(mapping["en1_organization_id"], 3)
        reg = json.loads((self.root / "registry.json").read_text(encoding="utf-8"))
        relatic = next(r for r in reg["tenants"] if r["tenant_id"] == "relatic")
        self.assertEqual(relatic["en1_organization_id"], 3)


if __name__ == "__main__":
    unittest.main()
