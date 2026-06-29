#!/usr/bin/env python3
"""Contract tests — mismo comportamiento Memory vs JSON (puerto MarketingPlanRepository)."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import (  # noqa: E402
    PlanPriority,
    PlanStatus,
    StrategyType,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import (  # noqa: E402
    Budget,
    DateRange,
    MarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.json_repository import (  # noqa: E402
    JsonMarketingPlanRepository,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.mapper import (  # noqa: E402
    plan_to_record,
    record_to_plan,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.memory import (  # noqa: E402
    InMemoryMarketingPlanRepository,
)


def _sample_plan(
    plan_id: str = "mpl_001",
    *,
    estado: PlanStatus = PlanStatus.BORRADOR,
    nombre: str = "Plan Q3 EN1",
    activated_at: datetime | None = None,
) -> MarketingPlan:
    now = datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    return MarketingPlan(
        id=plan_id,
        tenant_id="easytech",
        app_id="en1",
        nombre=nombre,
        objetivo_general="Incrementar leads cualificados en el segmento PYME",
        strategy_type=StrategyType.LEAD_GENERATION,
        north_star_metric="Leads cualificados mensuales",
        success_criteria=["100 leads", "20 reuniones"],
        publico_objetivo=["Gerentes PYME", "Contadores"],
        marketing_brief="Propuesta de valor EN1 y restricciones de presupuesto.",
        periodo=DateRange(date(2026, 7, 1), date(2026, 9, 30)),
        budget=Budget(Decimal("5000"), "USD"),
        estado=estado,
        prioridad=PlanPriority.ALTA,
        created_at=now,
        updated_at=now,
        created_by="admin@easytech",
        observaciones="",
        activated_at=activated_at,
    )


class RepositoryContractMixin:
    def test_save_and_get_by_id(self):
        plan = _sample_plan()
        self.repo.save(plan)
        loaded = self.repo.get_by_id(plan.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.id, plan.id)
        self.assertEqual(loaded.nombre, plan.nombre)
        self.assertEqual(loaded.budget.amount, plan.budget.amount)

    def test_get_by_id_missing_returns_none(self):
        self.assertIsNone(self.repo.get_by_id("missing"))

    def test_save_overwrites_same_id(self):
        plan = _sample_plan()
        self.repo.save(plan)
        updated = plan.copy()
        updated.nombre = "Plan actualizado"
        self.repo.save(updated)
        loaded = self.repo.get_by_id(plan.id)
        assert loaded is not None
        self.assertEqual(loaded.nombre, "Plan actualizado")

    def test_find_active_returns_active_plan(self):
        borrador = _sample_plan("mpl_b", nombre="Borrador")
        activo = _sample_plan(
            "mpl_a",
            nombre="Activo",
            estado=PlanStatus.ACTIVO,
            activated_at=datetime(2026, 6, 26, 13, 0, 0, tzinfo=timezone.utc),
        )
        self.repo.save(borrador)
        self.repo.save(activo)
        found = self.repo.find_active("easytech", "en1")
        assert found is not None
        self.assertEqual(found.id, "mpl_a")

    def test_find_active_none_when_no_active(self):
        self.repo.save(_sample_plan())
        self.assertIsNone(self.repo.find_active("easytech", "en1"))

    def test_list_plans_filters_by_estado(self):
        self.repo.save(_sample_plan("mpl_1", nombre="Uno"))
        self.repo.save(
            _sample_plan(
                "mpl_2",
                nombre="Dos",
                estado=PlanStatus.ACTIVO,
                activated_at=datetime(2026, 6, 26, 13, 0, 0, tzinfo=timezone.utc),
            )
        )
        borradores = self.repo.list_plans("easytech", app_id="en1", estado=PlanStatus.BORRADOR)
        activos = self.repo.list_plans("easytech", app_id="en1", estado=PlanStatus.ACTIVO)
        self.assertEqual(len(borradores), 1)
        self.assertEqual(len(activos), 1)
        self.assertEqual(borradores[0].id, "mpl_1")
        self.assertEqual(activos[0].id, "mpl_2")

    def test_list_plans_all_apps_in_tenant(self):
        plan_a = _sample_plan("mpl_a")
        plan_b = _sample_plan("mpl_b")
        plan_b.app_id = "default"
        self.repo.save(plan_a)
        self.repo.save(plan_b)
        rows = self.repo.list_plans("easytech")
        self.assertEqual(len(rows), 2)

    def test_mapper_roundtrip(self):
        plan = _sample_plan()
        restored = record_to_plan(plan_to_record(plan))
        self.assertEqual(restored.id, plan.id)
        self.assertEqual(restored.estado, plan.estado)
        self.assertEqual(restored.success_criteria, plan.success_criteria)


class MemoryRepositoryContractTests(RepositoryContractMixin, unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryMarketingPlanRepository()


class JsonRepositoryContractTests(RepositoryContractMixin, unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.repo = JsonMarketingPlanRepository(Path(self._tmpdir))

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
