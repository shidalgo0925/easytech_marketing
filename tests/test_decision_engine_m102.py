#!/usr/bin/env python3
"""Tests M10.2 — Decision Engine PriorityScorer."""

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

from Motor_Tecnico.accio_engine.brand_domain.model import Brand  # noqa: E402
from Motor_Tecnico.accio_engine.company_brain_domain.model import CompanyBrain  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_domain.model import RecommendationCandidate  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_domain.snapshot import KnowledgeSnapshot  # noqa: E402
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.composition import (  # noqa: E402
    build_candidates_use_case,
    reset_decision_engine,
    tenant_context,
)
from Motor_Tecnico.accio_engine.decision_engine_infrastructure.priority_scorer import PriorityScorer  # noqa: E402
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema  # noqa: E402


def _registry(apps: list[dict]) -> dict:
    return {
        "version": 1,
        "default_app_id": apps[0]["app_id"],
        "apps": apps,
    }


class DecisionEngineM102Test(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="de_m102_")
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
            json.dumps(
                {
                    "productos_servicios": [
                        "Odoo ERP",
                        "EasyNodeOne (EN1) — plataforma todo en uno",
                        "EPOSOne",
                    ],
                    "objetivos_comerciales": ["Generar diagnósticos"],
                }
            ),
            encoding="utf-8",
        )
        (apps_dir / "registry.json").write_text(
            json.dumps(
                _registry(
                    [
                        {"app_id": "default", "name": "EasyTech", "slug": "default", "status": "active", "is_default": True},
                        {"app_id": "en1", "name": "EN1", "slug": "en1", "status": "active", "is_default": False},
                        {"app_id": "eposone", "name": "EPOSOne", "slug": "eposone", "status": "active", "is_default": False},
                    ]
                )
            ),
            encoding="utf-8",
        )

        def _queue(app_id: str, last_published: str | None, content_type: str) -> dict:
            posts = []
            if last_published:
                posts.append(
                    {
                        "id": f"pub_{app_id}",
                        "platform": "linkedin",
                        "status": "published",
                        "published_at": last_published,
                        "text": f"Publicado {app_id}",
                        "app_id": app_id,
                    }
                )
            posts.append(
                {
                    "id": f"post_{app_id}",
                    "platform": "linkedin",
                    "status": "pending",
                    "scheduled_at": "2026-07-24T13:00:00-05:00",
                    "content_type": content_type,
                    "text": f"Post {app_id}",
                    "app_id": app_id,
                }
            )
            return {"posts": posts}

        for app_id, last_pub, ctype in [
            ("en1", "2026-06-12T10:00:00-05:00", "venta"),
            ("eposone", "2026-06-19T10:00:00-05:00", "valor"),
        ]:
            path = apps_dir / app_id / "content_queue.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(_queue(app_id, last_pub, ctype)), encoding="utf-8")

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
        default_dir = apps_dir / "default"
        default_dir.mkdir(parents=True, exist_ok=True)
        (default_dir / "content_queue.json").write_text(json.dumps(default_queue), encoding="utf-8")

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

    def test_candidates_have_priority_score_and_factors(self) -> None:
        ctx = tenant_context(self.tenant_id)
        candidates = build_candidates_use_case()(ctx, reference_at=self.reference_at)
        self.assertGreaterEqual(len(candidates), 2)
        for row in candidates:
            self.assertGreater(row.priority_score, 0.0)
            self.assertIn(row.priority, {"high", "medium", "low"})
            factors = row.justification_refs.get("priority_factors")
            self.assertIsInstance(factors, dict)
            self.assertIn("inactivity", factors)

    def test_deterministic_ordering(self) -> None:
        ctx = tenant_context(self.tenant_id)
        uc = build_candidates_use_case()
        first = [c.brand_id for c in uc(ctx, reference_at=self.reference_at)]
        second = [c.brand_id for c in uc(ctx, reference_at=self.reference_at)]
        self.assertEqual(first, second)
        scores = [c.priority_score for c in uc(ctx, reference_at=self.reference_at)]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_en1_ranks_above_eposone_with_longer_gap(self) -> None:
        ctx = tenant_context(self.tenant_id)
        candidates = build_candidates_use_case()(ctx, reference_at=self.reference_at)
        by_brand = {c.brand_id: c for c in candidates}
        self.assertIn("en1", by_brand)
        self.assertIn("eposone", by_brand)
        en1_idx = next(i for i, c in enumerate(candidates) if c.brand_id == "en1")
        epos_idx = next(i for i, c in enumerate(candidates) if c.brand_id == "eposone")
        self.assertLess(en1_idx, epos_idx)
        self.assertGreater(by_brand["en1"].priority_score, by_brand["eposone"].priority_score)

    def test_unit_scorer_product_alignment(self) -> None:
        brand = Brand(
            tenant_id=self.tenant_id,
            brand_id="en1",
            company_id=self.tenant_id,
            slug="en1",
            name="EN1",
            legacy_app_id="en1",
        )
        brain = CompanyBrain(
            tenant_id=self.tenant_id,
            company_id=self.tenant_id,
            profile={"productos_servicios": ["Odoo", "EasyNodeOne (EN1)"]},
            status="published",
            updated_at="2026-06-20",
        )
        snapshot = KnowledgeSnapshot(
            tenant_id=self.tenant_id,
            company_id=self.tenant_id,
            generated_at=KnowledgeSnapshot.now_iso(),
            brands=(brand,),
            company_brain=brain,
        )
        candidate = RecommendationCandidate(
            brand_id="en1",
            title="Publicar EN1",
            description="",
            action="publish",
            reason="gap",
            priority="high",
            owner_role="marketing",
            source="rule:test",
            justification_refs={"days_since_last_published": 10, "content_type": "venta"},
        )
        scored = PriorityScorer().score(candidate, snapshot, reference_at=self.reference_at)
        alignment = scored.justification_refs["priority_factors"]["product_alignment"]
        self.assertGreaterEqual(alignment, 0.7)


if __name__ == "__main__":
    unittest.main()
