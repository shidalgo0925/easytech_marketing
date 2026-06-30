#!/usr/bin/env python3
"""Tests M10.3 — Recommendation persistence + API + Memory."""

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
from Motor_Tecnico.accio_engine.decision_engine_api.composition import (  # noqa: E402
    decision_engine_use_cases,
    reset_decision_engine,
    tenant_context,
)
from Motor_Tecnico.accio_engine.decision_engine_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


class DecisionEngineM103Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="de_m103_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "rectenant"
        ensure_schema()
        reset_decision_engine()
        reset_use_cases_cache()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@rec"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        self.patches = [
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
        ]
        for p in self.patches:
            p.start()

        self.candidate = RecommendationCandidate(
            brand_id="en1",
            title="Publicar EN1",
            description="Post pendiente en cola",
            action="publish",
            reason="Sin publicaciones en 9 días",
            priority="high",
            owner_role="marketing",
            source="rule:brand_publication_gap",
            confidence=1.0,
            priority_score=0.82,
            justification_refs={
                "brand_id": "en1",
                "publication_id": "linkedin_11_en1_demo",
                "days_since_last_published": 9,
            },
        )

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_decision_engine()
        reset_use_cases_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_MEMORY_STORE", None)

    def test_schema_v10_recommendations(self) -> None:
        conn = get_connection()
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
        finally:
            conn.close()
        self.assertIn("recommendations", tables)
        self.assertIn(10, versions)

    def test_create_from_candidate_and_list_api(self) -> None:
        ctx = tenant_context(self.tenant_id)
        uc = decision_engine_use_cases()
        created = uc.create_from_candidate(ctx, self.candidate)
        self.assertTrue(created.recommendation_id.startswith("rec_"))
        self.assertEqual(created.status, "pending_approval")
        self.assertEqual(created.brand_id, "en1")
        self.assertEqual(created.priority_score, 0.82)

        resp = self.client.get(f"/api/v1/tenants/{self.tenant_id}/recommendations?brand_id=en1")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["recommendation_id"], created.recommendation_id)
        self.assertEqual(data[0]["action"], "publish")
        self.assertEqual(data[0]["justification_refs"]["publication_id"], "linkedin_11_en1_demo")

    def test_get_recommendation_api(self) -> None:
        ctx = tenant_context(self.tenant_id)
        created = decision_engine_use_cases().create_from_candidate(ctx, self.candidate)
        resp = self.client.get(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{created.recommendation_id}"
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        row = resp.get_json()["data"]
        self.assertEqual(row["title"], "Publicar EN1")
        self.assertEqual(row["owner_role"], "marketing")
        self.assertEqual(row["source"], "rule:brand_publication_gap")

    def test_recommendation_created_memory_event(self) -> None:
        ctx = tenant_context(self.tenant_id)
        decision_engine_use_cases().create_from_candidate(ctx, self.candidate)
        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT event_type, payload_json FROM memory_events
                WHERE tenant_id = ? AND event_type = 'RecommendationCreated'
                ORDER BY timestamp DESC LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "RecommendationCreated")
        payload = json.loads(row[1])
        self.assertEqual(payload["action"], "publish")
        self.assertEqual(payload["priority"], "high")


if __name__ == "__main__":
    unittest.main()
