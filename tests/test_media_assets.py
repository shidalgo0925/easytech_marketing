#!/usr/bin/env python3
"""Tests M8 — Media assets (flyers)."""

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
from Motor_Tecnico.accio_engine import dashboard_data  # noqa: E402
from Motor_Tecnico.accio_engine.media_asset_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.media_asset_infrastructure.facade import reset_media_asset_service  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


SAMPLE_MANIFEST = {
    "version": 1,
    "updated": "2026-06-19",
    "contact": {"email": "info@easytech.services"},
    "flyers": [
        {"num": 5, "file": "05_en1_plataforma.png", "topic": "EasyNodeOne EN1"},
        {"num": 10, "file": None, "topic": "IIUS", "status": "missing"},
    ],
    "extras": [
        {"file": "00_landing_ecosistema.png", "topic": "Landing hub"},
    ],
}


class MediaAssetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="asset_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_ASSET_STORE"] = "dual"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        flyers_dir = self.tenant_root / "flyers"
        flyers_dir.mkdir(parents=True)
        (flyers_dir / "manifest.json").write_text(json.dumps(SAMPLE_MANIFEST), encoding="utf-8")
        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "content_queue.json").write_text(json.dumps({"posts": []}), encoding="utf-8")

        reset_use_cases_cache()
        reset_media_asset_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _effective_paths(tid, app_id=None):
            return {
                "flyers_manifest": self.tenant_root / "flyers" / "manifest.json",
                "flyers_dir": self.tenant_root / "flyers",
                "content_queue": self.tenant_root / "content_queue.json",
                "calendar": self.tenant_root / "calendar.json",
                "campaigns": self.tenant_root / "campaigns.json",
                "knowledge_dir": self.tenant_root / "knowledge",
                "knowledge_manifest": self.tenant_root / "knowledge" / "manifest.json",
            }

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.dashboard_data.effective_paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.dashboard_data._paths", lambda tid, app_id=None: _effective_paths(tid)),
            patch("Motor_Tecnico.accio_engine.executor.load_content_queue_for_app", return_value={"posts": []}),
            patch("Motor_Tecnico.accio_engine.media_asset_infrastructure.json_repository.effective_paths", _effective_paths),
            patch("Motor_Tecnico.accio_engine.media_asset_infrastructure.json_repository.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@asset"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_media_asset_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_ASSET_STORE", None)

    def test_schema_v8_media_assets(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("media_assets", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.media_asset_infrastructure.legacy_mapper import manifest_to_assets
        from Motor_Tecnico.accio_engine.media_asset_infrastructure.sqlite_repository import SqliteMediaAssetRepository

        assets = manifest_to_assets(self.tenant_id, SAMPLE_MANIFEST)
        SqliteMediaAssetRepository().save_all_for_tenant(self.tenant_id, assets)
        reset_media_asset_service()
        reset_use_cases_cache()
        os.environ["ACCIO_ASSET_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/assets?type=flyer")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 2)
        ids = {row["asset_id"] for row in data}
        self.assertIn("flyer_05", ids)
        self.assertIn("flyer_10", ids)

    def test_dashboard_load_flyers_library_sql(self) -> None:
        from Motor_Tecnico.accio_engine.media_asset_infrastructure.legacy_mapper import manifest_to_assets
        from Motor_Tecnico.accio_engine.media_asset_infrastructure.sqlite_repository import SqliteMediaAssetRepository

        assets = manifest_to_assets(self.tenant_id, SAMPLE_MANIFEST)
        SqliteMediaAssetRepository().save_all_for_tenant(self.tenant_id, assets)
        reset_media_asset_service()
        os.environ["ACCIO_ASSET_STORE"] = "sql"

        library = dashboard_data.load_flyers_library(self.tenant_id)
        self.assertEqual(library["total"], 2)
        self.assertEqual(library["missing"], 1)
        self.assertEqual(library["available"], 1)


if __name__ == "__main__":
    unittest.main()
