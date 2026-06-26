#!/usr/bin/env python3
"""Tests de aprovisionamiento de empresas (tenants)."""

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

from Motor_Tecnico.accio_engine import tenant_provisioning  # noqa: E402
from Motor_Tecnico.accio_engine.tenant import TenantNotFoundError  # noqa: E402


class TenantProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = Path(self.tmp) / "tenants"
        self.root.mkdir()
        self.registry = self.root / "registry.json"
        self.registry.write_text(
            json.dumps(
                {
                    "version": 2,
                    "tenants": [
                        {
                            "tenant_id": "easytech",
                            "display_name": "EasyTech",
                            "status": "active",
                            "crm_target": "odoo",
                            "timezone": "America/Panama",
                            "domains": [],
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.root / "easytech").mkdir()
        (self.root / "easytech" / "business_context.json").write_text(
            json.dumps({"empresa": "EasyTech", "industria": "TI"}),
            encoding="utf-8",
        )

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _patch_paths(self):
        return mock.patch.multiple(
            "Motor_Tecnico.accio_engine.tenant",
            TENANTS_ROOT=self.root,
            REGISTRY_PATH=self.registry,
        )

    def test_validate_tenant_id_rejects_invalid(self):
        with self.assertRaises(ValueError):
            tenant_provisioning.validate_tenant_id("1bad")
        with self.assertRaises(ValueError):
            tenant_provisioning.validate_tenant_id("")

    def test_create_and_get_company(self):
        with self._patch_paths():
            company = tenant_provisioning.create_company(
                {
                    "tenant_id": "acme_corp",
                    "display_name": "ACME Corp",
                    "crm_target": "odoo",
                    "domains": ["acme.test"],
                    "context": {
                        "empresa": "ACME Corp",
                        "industria": "Retail",
                        "pais": "Panamá",
                    },
                }
            )
            self.assertEqual(company["tenant_id"], "acme_corp")
            self.assertEqual(company["display_name"], "ACME Corp")
            loaded = tenant_provisioning.get_company("acme_corp")
            self.assertEqual(loaded["context"]["industria"], "Retail")
            self.assertTrue((self.root / "acme_corp" / "users.json").is_file())
            self.assertTrue((self.root / "acme_corp" / "content_queue.json").is_file())

    def test_duplicate_tenant_raises(self):
        with self._patch_paths():
            tenant_provisioning.create_company({"tenant_id": "dup_co", "display_name": "Dup"})
            with self.assertRaises(ValueError):
                tenant_provisioning.create_company({"tenant_id": "dup_co", "display_name": "Dup 2"})

    def test_update_company(self):
        with self._patch_paths():
            tenant_provisioning.create_company({"tenant_id": "upd_co", "display_name": "Old Name"})
            updated = tenant_provisioning.update_company(
                "upd_co",
                {"display_name": "New Name", "context": {"industria": "Logística"}},
            )
            self.assertEqual(updated["display_name"], "New Name")
            self.assertEqual(updated["context"]["industria"], "Logística")

    def test_disable_protected_raises(self):
        with self._patch_paths():
            with self.assertRaises(ValueError):
                tenant_provisioning.disable_company("easytech")

    def test_get_missing_raises(self):
        with self._patch_paths():
            with self.assertRaises(TenantNotFoundError):
                tenant_provisioning.get_company("no_existe")


if __name__ == "__main__":
    unittest.main()
