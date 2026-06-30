#!/usr/bin/env python3
"""Tests M10.1 — Decision Engine Roadmap Builder + brand_publication_gap."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.decision_engine_infrastructure.composition import (  # noqa: E402
    build_candidates_use_case,
    reset_decision_engine,
    tenant_context,
)
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.rules.brand_publication_gap import (  # noqa: E402
    RULE_ID,
    evaluate_brand_publication_gap,
)
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema  # noqa: E402


def _registry(apps: list[dict]) -> dict:
    return {
        "version": 1,
        "default_app_id": apps[0]["app_id"],
        "apps": apps,
    }


class DecisionEngineM101Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="de_m101_")
        self.db_path = Path(self.tmp) / "marketing_os.db"
        os.environ["ACCIO_PLATFORM_DB"] = str(self.db_path)
        os.environ["ACCIO_BRAND_STORE"] = "dual"
        os.environ["ACCIO_PUBLICATION_STORE"] = "dual"
        os.environ["ACCIO_BRAIN_STORE"] = "dual"

        self.tenant_id = "easytech"
        self.tenant_root = Path(self.tmp) / "tenants" / self.tenant_id
        apps_dir = self.tenant_root / "apps"
        apps_dir.mkdir(parents=True)

        (self.tenant_root / "tenant.json").write_text(
            json.dumps({"tenant_id": self.tenant_id}),
            encoding="utf-8",
        )
        (self.tenant_root / "business_context.json").write_text(
            json.dumps({"productos_servicios": ["EasyNodeOne (EN1)"]}),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                _registry(
                    [
                        {
                            "app_id": "default",
                            "name": "EasyTech",
                            "slug": "default",
                            "status": "active",
                            "is_default": True,
                        },
                        {
                            "app_id": "en1",
                            "name": "EN1",
                            "slug": "en1",
                            "status": "active",
                            "is_default": False,
                        },
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
                    "text": "Post EN1 pendiente",
                    "flyer": "flyers/05_en1_plataforma.png",
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
                    "text": "Post reciente default",
                    "app_id": "default",
                }
            ]
        }
        (apps_dir / "en1" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "en1" / "content_queue.json").write_text(json.dumps(en1_queue), encoding="utf-8")
        (apps_dir / "default" / "content_queue.json").parent.mkdir(parents=True, exist_ok=True)
        (apps_dir / "default" / "content_queue.json").write_text(json.dumps(default_queue), encoding="utf-8")

        ensure_schema()
        reset_decision_engine()

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
        ]
        for p in self.patches:
            p.start()

        self.reference_at = datetime(2026, 6, 26, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        for p in self.patches:
            p.stop()
        reset_decision_engine()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_brand_publication_gap_detects_en1(self) -> None:
        ctx = tenant_context(self.tenant_id)
        candidates = build_candidates_use_case()(ctx, reference_at=self.reference_at)

        en1 = [c for c in candidates if c.brand_id == "en1"]
        self.assertEqual(len(en1), 1, candidates)
        row = en1[0]
        self.assertEqual(row.action, "publish")
        self.assertIn(row.priority, {"high", "medium", "low"})
        self.assertGreater(row.priority_score, 0.0)
        self.assertEqual(row.owner_role, "marketing")
        self.assertEqual(row.source, f"rule:{RULE_ID}")
        self.assertIn("EN1", row.title)
        self.assertIn("días", row.reason)
        self.assertEqual(row.justification_refs.get("publication_id"), "linkedin_11_en1_demo")

    def test_skips_brand_with_recent_publish(self) -> None:
        ctx = tenant_context(self.tenant_id)
        candidates = build_candidates_use_case()(ctx, reference_at=self.reference_at)
        default = [c for c in candidates if c.brand_id == "default"]
        self.assertEqual(default, [])

    def test_rule_unit_never_published_with_pending(self) -> None:
        from Motor_Tecnico.accio_engine.brand_domain.model import Brand
        from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot
        from Motor_Tecnico.accio_engine.publication_domain.model import Publication

        brand = Brand(
            tenant_id=self.tenant_id,
            brand_id="en1",
            company_id=self.tenant_id,
            slug="en1",
            name="EN1",
            legacy_app_id="en1",
        )
        pub = Publication(
            tenant_id=self.tenant_id,
            publication_id="pending_1",
            brand_id="en1",
            channel="linkedin",
            body="x",
            status="pending",
            scheduled_at="2026-07-01T10:00:00-05:00",
        )
        snapshot = KnowledgeSnapshot(
            tenant_id=self.tenant_id,
            company_id=self.tenant_id,
            generated_at=KnowledgeSnapshot.now_iso(),
            brands=(brand,),
            publications_by_brand={"en1": (pub,)},
        )
        rows = evaluate_brand_publication_gap(snapshot, reference_at=self.reference_at)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].brand_id, "en1")


if __name__ == "__main__":
    unittest.main()
