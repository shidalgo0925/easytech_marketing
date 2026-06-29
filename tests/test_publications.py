#!/usr/bin/env python3
"""Tests M4 — Publications."""

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
from Motor_Tecnico.accio_engine import executor  # noqa: E402
from Motor_Tecnico.accio_engine.publication_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.publication_infrastructure.facade import reset_publication_service  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


SAMPLE_QUEUE = {
    "posts": [
        {
            "id": "linkedin_test_01",
            "platform": "linkedin",
            "status": "scheduled",
            "scheduled_at": "2026-07-01T10:00:00-05:00",
            "text": "Post de prueba",
            "flyer": "flyers/01_desarrollo_software.png",
            "app_id": "default",
        }
    ]
}


class PublicationsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="pub_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"

        self.tenant_id = "pubtenant"
        self.app_id = "default"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps" / self.app_id
        apps_dir.mkdir(parents=True)
        (apps_dir / "content_queue.json").write_text(json.dumps(SAMPLE_QUEUE), encoding="utf-8")
        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )
        (self.tenant_root / "apps" / "registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_app_id": "default",
                    "apps": [{"app_id": "default", "name": "Principal", "status": "active", "is_default": True}],
                }
            ),
            encoding="utf-8",
        )

        reset_use_cases_cache()
        reset_publication_service()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            return {"content_queue": root / "content_queue.json"}

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.marketing_app.effective_app_paths", _app_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.default_app_id", return_value="default"),
            patch("Motor_Tecnico.accio_engine.marketing_app.normalize_app_id", side_effect=lambda x: x or "default"),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@pub"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_use_cases_cache()
        reset_publication_service()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_PUBLICATION_STORE", None)

    def test_schema_v4_publications(self) -> None:
        ensure_schema()
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        self.assertIn("publications", tables)

    def test_migrate_and_list_api(self) -> None:
        from Motor_Tecnico.accio_engine.publication_infrastructure.legacy_mapper import queue_to_publications
        from Motor_Tecnico.accio_engine.publication_infrastructure.sqlite_repository import SqlitePublicationRepository

        pubs = queue_to_publications(self.tenant_id, self.app_id, SAMPLE_QUEUE)
        SqlitePublicationRepository().save_all_for_tenant(self.tenant_id, self.app_id, pubs)
        reset_publication_service()
        reset_use_cases_cache()
        os.environ["ACCIO_PUBLICATION_STORE"] = "sql"

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/apps/{self.app_id}/publications")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "linkedin_test_01")

    def test_executor_delegates_to_sql(self) -> None:
        from Motor_Tecnico.accio_engine.publication_infrastructure.legacy_mapper import queue_to_publications
        from Motor_Tecnico.accio_engine.publication_infrastructure.sqlite_repository import SqlitePublicationRepository

        pubs = queue_to_publications(self.tenant_id, self.app_id, SAMPLE_QUEUE)
        SqlitePublicationRepository().save_all_for_tenant(self.tenant_id, self.app_id, pubs)
        reset_publication_service()
        os.environ["ACCIO_PUBLICATION_STORE"] = "sql"

        queue = executor.load_content_queue(self.tenant_id, self.app_id)
        self.assertEqual(len(queue.get("posts", [])), 1)
        self.assertEqual(queue["posts"][0]["id"], "linkedin_test_01")


if __name__ == "__main__":
    unittest.main()
