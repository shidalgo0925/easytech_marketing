#!/usr/bin/env python3
"""Tests M3 — Brands."""

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
from Motor_Tecnico.accio_engine.brand_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.brand_infrastructure.facade import reset_brand_service  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_app import get_app, list_apps  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


class BrandsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="brand_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"

        self.tenant_id = "brandtenant"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)
        (apps_dir / "registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_app_id": "default",
                    "apps": [
                        {
                            "app_id": "default",
                            "name": "Principal",
                            "slug": "default",
                            "status": "active",
                            "is_default": True,
                        },
                        {
                            "app_id": "en1",
                            "name": "Easy NodeOne",
                            "slug": "en1",
                            "status": "active",
                            "is_default": False,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )

        reset_use_cases_cache()
        reset_brand_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch(
                "Motor_Tecnico.accio_engine.marketing_app.registry_path",
                lambda tid: self.tenant_root / "apps" / "registry.json",
            ),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@brand"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_brand_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_BRAND_STORE", None)

    def test_schema_v3_brands(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("brands", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.brand_infrastructure.legacy_mapper import registry_to_brands
        from Motor_Tecnico.accio_engine.brand_infrastructure.sqlite_repository import SqliteBrandRepository

        brands = registry_to_brands(self.tenant_id)
        SqliteBrandRepository().save_all(self.tenant_id, brands)
        reset_brand_service()
        reset_use_cases_cache()
        os.environ["ACCIO_BRAND_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/brands")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 2)
        ids = {row["legacy_app_id"] for row in data}
        self.assertIn("default", ids)
        self.assertIn("en1", ids)

    def test_marketing_app_delegates_to_sql(self) -> None:
        from Motor_Tecnico.accio_engine.brand_infrastructure.legacy_mapper import registry_to_brands
        from Motor_Tecnico.accio_engine.brand_infrastructure.sqlite_repository import SqliteBrandRepository

        brands = registry_to_brands(self.tenant_id)
        SqliteBrandRepository().save_all(self.tenant_id, brands)
        reset_brand_service()
        os.environ["ACCIO_BRAND_STORE"] = "sql"

        apps = list_apps(self.tenant_id)
        self.assertEqual(len(apps), 2)
        app_en1 = get_app(self.tenant_id, "en1")
        self.assertEqual(app_en1.name, "Easy NodeOne")


if __name__ == "__main__":
    unittest.main()
