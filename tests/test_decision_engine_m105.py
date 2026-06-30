#!/usr/bin/env python3
"""Tests M10.5 — Approval Queue (approve / reject / snooze)."""

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


class DecisionEngineM105Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="de_m105_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_MEMORY_STORE"] = "sql"

        self.tenant_id = "approvaltenant"
        ensure_schema()
        reset_decision_engine()
        reset_use_cases_cache()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "marketing@ets"
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
            description="Post pendiente",
            action="publish",
            reason="Sin publicaciones en 9 días",
            priority="high",
            owner_role="marketing",
            source="rule:brand_publication_gap",
            priority_score=0.8,
        )
        ctx = tenant_context(self.tenant_id)
        self.rec = decision_engine_use_cases().create_from_candidate(ctx, self.candidate)
        self.rec_id = self.rec.recommendation_id

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_decision_engine()
        reset_use_cases_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)
        os.environ.pop("ACCIO_PLATFORM_DB", None)
        os.environ.pop("ACCIO_MEMORY_STORE", None)

    def test_approve_changes_status_and_memory(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{self.rec_id}/approve"
        )
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        data = resp.get_json()["data"]
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["approved_by"], "marketing@ets")

        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT event_type FROM memory_events
                WHERE tenant_id = ? AND event_type = 'RecommendationAccepted'
                ORDER BY timestamp DESC LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)

    def test_reject_requires_reason(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{self.rec_id}/reject",
            json={},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["error"], "rejection_reason_required")

    def test_reject_with_reason(self) -> None:
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{self.rec_id}/reject",
            json={"reason": "No es prioridad esta semana"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()["data"]
        self.assertEqual(data["status"], "rejected")
        self.assertEqual(data["result"]["rejection_reason"], "No es prioridad esta semana")

        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT event_type, payload_json FROM memory_events
                WHERE tenant_id = ? AND event_type = 'RecommendationRejected'
                ORDER BY timestamp DESC LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(json.loads(row[1])["reason"], "No es prioridad esta semana")

    def test_snooze_sets_until(self) -> None:
        ctx = tenant_context(self.tenant_id)
        rec2 = decision_engine_use_cases().create_from_candidate(ctx, self.candidate)
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{rec2.recommendation_id}/snooze",
            json={"until": "2026-07-15T09:00:00-05:00"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()["data"]
        self.assertEqual(data["status"], "snoozed")
        self.assertEqual(data["due_at"], "2026-07-15T09:00:00-05:00")

    def test_cannot_approve_already_approved(self) -> None:
        self.client.post(f"/api/v1/tenants/{self.tenant_id}/recommendations/{self.rec_id}/approve")
        resp = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/recommendations/{self.rec_id}/approve"
        )
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.get_json()["error"], "invalid_recommendation_transition")


if __name__ == "__main__":
    unittest.main()
