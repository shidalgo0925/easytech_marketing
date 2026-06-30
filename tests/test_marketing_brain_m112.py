#!/usr/bin/env python3
"""Tests M11.2 — enrich daily roadmap (bulk)."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.app import app  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.composition import reset_decision_engine  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_api.routes import reset_use_cases_cache as reset_de_cache  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_brain_api.routes import reset_use_cases_cache  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_brain_domain.model import RecommendationEnrichment  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_connection  # noqa: E402


def _registry(apps: list[dict]) -> dict:
    return {
        "version": 1,
        "default_app_id": apps[0]["app_id"],
        "apps": apps,
    }


class MarketingBrainM112Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="mb_m112_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"
        os.environ["ACCIO_MEMORY_STORE"] = "sql"
        os.environ["AI_ASSISTANT_ENABLED"] = "true"
        os.environ["ACCIO_AI_BASE_URL"] = "http://codito:4000"

        self.tenant_id = "easytech"
        self.roadmap_date = "2026-06-26"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)

        (self.tenant_root / "tenant.json").write_text(json.dumps({"tenant_id": self.tenant_id}), encoding="utf-8")
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"productos_servicios": ["EasyNodeOne (EN1)"]}),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                _registry(
                    [
                        {"app_id": "default", "name": "EasyTech", "slug": "default", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "slug": "en1", "status": "active", "is_default": False},
                    ]
                )
            ),
            encoding="utf-8",
        )

        en1_queue = {
            "posts": [
                {
                    "id": "linkedin_11_en1_demo",
                    "platform": "linkedin",
                    "status": "pending",
                    "scheduled_at": "2026-07-24T13:00:00-05:00",
                    "content_type": "venta",
                    "text": "Post EN1",
                    "app_id": "en1",
                }
            ]
        }
        default_queue = {
            "posts": [
                {
                    "id": "linkedin_recent",
                    "platform": "linkedin",
                    "status": "published",
                    "published_at": "2026-06-20T10:00:00-05:00",
                    "text": "Reciente",
                    "app_id": "default",
                }
            ]
        }
        for app_id, queue in [("en1", en1_queue), ("default", default_queue)]:
            path = apps_dir / app_id / "content_queue.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(queue), encoding="utf-8")

        ensure_schema()
        reset_decision_engine()
        reset_de_cache()
        reset_use_cases_cache()

        tenant_obj = type("T", (), {"tenant_id": self.tenant_id, "root": self.tenant_root})()

        def _paths(_tid: str) -> dict:
            return {
                "business_context": self.tenant_root / "business_context.json",
                "editorial_rules": self.tenant_root / "editorial_rules.json",
            }

        def _app_paths(tid, aid=None):
            aid = aid or "default"
            root = self.tenant_root / "apps" / aid
            return {"content_queue": root / "content_queue.json"}

        self.patches = [
            patch("Motor_Tecnico.accio_engine.tenant.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.tenant.TENANTS_ROOT", Path(self.tmp) / "tenants"),
            patch("Motor_Tecnico.accio_engine.tenant.effective_paths", side_effect=lambda t: _paths(t.tenant_id)),
            patch("Motor_Tecnico.accio_engine.marketing_app.resolve_tenant", return_value=tenant_obj),
            patch("Motor_Tecnico.accio_engine.marketing_app.effective_app_paths", _app_paths),
            patch("Motor_Tecnico.accio_engine.marketing_app.default_app_id", return_value="default"),
            patch("Motor_Tecnico.accio_engine.marketing_app.normalize_app_id", side_effect=lambda x: x or "default"),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.resolve_tenant",
                return_value=tenant_obj,
            ),
            patch(
                "Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper.effective_paths",
                side_effect=lambda t: _paths(t.tenant_id),
            ),
            patch("Motor_Tecnico.accio_engine.app._user_can_access_tenant", return_value=True),
            patch("Motor_Tecnico.accio_engine.app._check_request_permission", return_value=(True, None)),
            patch(
                "Motor_Tecnico.accio_engine.decision_engine_api.routes.tenant_today_iso",
                return_value=self.roadmap_date,
            ),
            patch(
                "Motor_Tecnico.accio_engine.marketing_brain_api.routes.tenant_today_iso",
                return_value=self.roadmap_date,
            ),
        ]
        for p in self.patches:
            p.start()

        self.client = app.test_client()
        with self.client.session_transaction() as sess:
            sess["accio_auth"] = True
            sess["user_id"] = "admin@brain"
            sess["role"] = "admin"
            sess["tenant_id"] = self.tenant_id
            sess["auth_method"] = "session"

        self.llm_patch = patch(
            "Motor_Tecnico.accio_engine.marketing_brain_infrastructure.llm_client.AiProviderMarketingBrainLLM.enrich_recommendation",
            side_effect=self._fake_enrich,
        )
        self.llm_patch.start()

    def _fake_enrich(self, rec):
        return RecommendationEnrichment(
            reason=f"IA: {rec.reason}",
            description=f"IA: {rec.description or rec.title}",
            confidence=0.85,
            model="test-model",
            narrative="Batch enrich",
        )

    def tearDown(self) -> None:
        self.llm_patch.stop()
        for p in self.patches:
            p.stop()
        reset_decision_engine()
        reset_de_cache()
        reset_use_cases_cache()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_enrich_roadmap_persists_all(self) -> None:
        gen = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/generate"
        )
        self.assertEqual(gen.status_code, 201)
        rec_count = len(gen.get_json()["data"]["recommendations"])

        enrich = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/enrich",
            json={"persist": True},
        )
        self.assertEqual(enrich.status_code, 200, enrich.get_data(as_text=True))
        body = enrich.get_json()["data"]
        self.assertEqual(body["enriched_count"], rec_count)
        self.assertEqual(body["failed_count"], 0)
        self.assertTrue(body["persisted"])
        self.assertTrue(all(item["enrichment"]["model"] == "test-model" for item in body["items"]))

        conn = get_connection()
        try:
            row = conn.execute(
                """
                SELECT justification_refs_json FROM recommendations
                WHERE tenant_id = ? LIMIT 1
                """,
                (self.tenant_id,),
            ).fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row)
        refs = json.loads(row[0])
        self.assertIn("ai_enrichment", refs)

    def test_skip_already_enriched(self) -> None:
        self.client.post(f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/generate")
        first = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/enrich",
            json={"persist": True},
        )
        self.assertEqual(first.status_code, 200)
        enriched_first = first.get_json()["data"]["enriched_count"]

        second = self.client.post(
            f"/api/v1/tenants/{self.tenant_id}/roadmaps/{self.roadmap_date}/enrich",
            json={"persist": True, "skip_enriched": True},
        )
        self.assertEqual(second.status_code, 200)
        body = second.get_json()["data"]
        self.assertEqual(body["enriched_count"], 0)
        self.assertEqual(body["skipped_count"], enriched_first)

    def test_enrich_missing_roadmap_404(self) -> None:
        resp = self.client.post(f"/api/v1/tenants/{self.tenant_id}/roadmaps/2099-01-01/enrich")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
