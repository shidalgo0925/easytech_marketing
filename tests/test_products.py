#!/usr/bin/env python3
"""Tests M5 — Products."""

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
from Motor_Tecnico.accio_engine import settings_center  # noqa: E402
from Motor_Tecnico.accio_engine.product_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.product_infrastructure.facade import reset_product_service  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


SAMPLE_PRODUCTS = {
    "version": 1,
    "products": [
        {
            "slug": "easynodeone_en1_plataforma_todo_en_uno",
            "name": "EasyNodeOne (EN1)",
            "enabled": True,
            "landing_path": "",
            "cta": "DIAGNÓSTICO",
        },
        {
            "slug": "consultor_a_ti_estrat_gica",
            "name": "Consultoría TI",
            "enabled": True,
            "landing_path": "",
            "cta": "DIAGNÓSTICO",
        },
    ],
}


class ProductsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="prod_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_PRODUCT_STORE"] = "dual"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        self.tenant_root.mkdir(parents=True)
        (self.tenant_root / "products.json").write_text(json.dumps(SAMPLE_PRODUCTS), encoding="utf-8")
        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )

        reset_use_cases_cache()
        reset_product_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.settings_center.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.product_infrastructure.json_repository.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@prod"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_product_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_PRODUCT_STORE", None)

    def test_schema_v5_products(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("products", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.product_infrastructure.legacy_mapper import catalog_to_products
        from Motor_Tecnico.accio_engine.product_infrastructure.sqlite_repository import SqliteProductRepository

        products = catalog_to_products(self.tenant_id, SAMPLE_PRODUCTS)
        SqliteProductRepository().save_all_for_tenant(self.tenant_id, products)
        reset_product_service()
        reset_use_cases_cache()
        os.environ["ACCIO_PRODUCT_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/apps/en1/products")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["slug"], "easynodeone_en1_plataforma_todo_en_uno")

    def test_settings_center_delegates_to_sql(self) -> None:
        from Motor_Tecnico.accio_engine.product_infrastructure.legacy_mapper import catalog_to_products
        from Motor_Tecnico.accio_engine.product_infrastructure.sqlite_repository import SqliteProductRepository

        products = catalog_to_products(self.tenant_id, SAMPLE_PRODUCTS)
        SqliteProductRepository().save_all_for_tenant(self.tenant_id, products)
        reset_product_service()
        os.environ["ACCIO_PRODUCT_STORE"] = "sql"

        data = settings_center.load_products(self.tenant_id)
        self.assertEqual(len(data.get("products", [])), 2)


if __name__ == "__main__":
    unittest.main()
