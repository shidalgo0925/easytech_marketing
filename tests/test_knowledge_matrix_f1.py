#!/usr/bin/env python3
"""Tests Knowledge Matrix — sectors.json + classify API."""

from __future__ import annotations

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
from Motor_Tecnico.accio_engine.knowledge_matrix_api.composition import reset_knowledge_matrix_service, reset_knowledge_matrix_use_cases  # noqa: E402
from Motor_Tecnico.accio_engine.knowledge_matrix_api.routes import reset_use_cases_cache  # noqa: E402


class KnowledgeMatrixF1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="km_f1_")
        self.tenant_id = "easytech"
        matrix_path = Path(self.tmp) / "Marketing" / "tenants" / self.tenant_id / "knowledge"
        matrix_path.mkdir(parents=True)
        shutil.copy(BASE / "Marketing" / "knowledge" / "sectors.json", matrix_path / "sectors.json")

        reset_knowledge_matrix_service()
        reset_knowledge_matrix_use_cases()
        reset_use_cases_cache()

        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch("Motor_Tecnico.accio_engine.knowledge_matrix_infrastructure.json_repository.BASE_DIR", Path(self.tmp)),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@km"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_knowledge_matrix_service()
        reset_knowledge_matrix_use_cases()
        reset_use_cases_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_matrix_has_sectors(self) -> None:
        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/knowledge-matrix")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()["data"]
        self.assertGreaterEqual(len(data["sectors"]), 5)
        self.assertIn("en1", data["brand_defaults"])

    def test_classify_by_brand(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/knowledge-matrix/classify",
            json={"brand_id": "eposone"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()["data"]
        self.assertEqual(body["product_slug"], "eposone")
        self.assertEqual(body["sector_id"], "retail")

    def test_classify_by_text(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/knowledge-matrix/classify",
            json={"text": "La universidad anuncia congreso de tesis académico"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()["data"]
        self.assertEqual(body["sector_id"], "educacion_superior")


if __name__ == "__main__":
    unittest.main()
