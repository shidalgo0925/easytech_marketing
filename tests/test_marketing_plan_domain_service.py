#!/usr/bin/env python3
"""Tests Pieza 3 — MarketingPlanDomainService (repositorio en memoria o JSON)."""

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

from Motor_Tecnico.accio_engine.marketing_plan_domain.commands import (  # noqa: E402
    ActivatePlanCommand,
    CompletePlanCommand,
    CreatePlanCommand,
    PausePlanCommand,
    UpdatePlanCommand,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import (  # noqa: E402
    ConflictResolution,
    PlanStatus,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import (  # noqa: E402
    DomainError,
    DomainErrorCode,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.events import (  # noqa: E402
    PlanActivated,
    PlanCompleted,
    PlanCreated,
    PlanPaused,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.json_repository import (  # noqa: E402
    JsonMarketingPlanRepository,
)
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.memory import (  # noqa: E402
    FixedClock,
    FixedIdGenerator,
    InMemoryMarketingPlanRepository,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import (  # noqa: E402
    MarketingPlanDomainService,
)


def _sample_create(**overrides) -> CreatePlanCommand:
    data = {
        "tenant_id": "easytech",
        "app_id": "en1",
        "nombre": "Plan Q3 EN1",
        "objetivo_general": "Incrementar leads cualificados en el segmento PYME",
        "strategy_type": "lead_generation",
        "north_star_metric": "Leads cualificados mensuales",
        "success_criteria": ["100 leads", "20 reuniones"],
        "publico_objetivo": ["Gerentes PYME", "Contadores"],
        "marketing_brief": (
            "Enfoque en propuesta de valor EN1, competencia local, "
            "dolores de facturación y restricciones de presupuesto."
        ),
        "periodo_inicio": date(2026, 7, 1),
        "periodo_fin": date(2026, 9, 30),
        "budget_amount": Decimal("5000"),
        "budget_currency": "USD",
        "prioridad": "alta",
        "created_by": "admin@easytech",
    }
    data.update(overrides)
    return CreatePlanCommand(**data)


class MarketingPlanDomainServiceTests(unittest.TestCase):
    _tmpdir: str | None = None

    def build_repository(self):
        return InMemoryMarketingPlanRepository()

    def setUp(self):
        self.repo = self.build_repository()
        self.clock = FixedClock(datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc))
        self.ids = FixedIdGenerator(
            plan_ids=["mpl_001", "mpl_002", "mpl_003", "mpl_004"],
            event_ids=["evt_001", "evt_002", "evt_003", "evt_004", "evt_005", "evt_006"],
        )
        self.service = MarketingPlanDomainService(
            repository=self.repo,
            clock=self.clock,
            id_generator=self.ids,
        )

    def tearDown(self):
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    def test_create_plan_emits_plan_created(self):
        result = self.service.create_plan(_sample_create())
        self.assertEqual(result.plan.id, "mpl_001")
        self.assertEqual(result.plan.estado, PlanStatus.BORRADOR)
        self.assertEqual(len(result.events), 1)
        self.assertIsInstance(result.events[0], PlanCreated)

    def test_invalid_date_range_raises(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(
                _sample_create(periodo_inicio=date(2026, 10, 1), periodo_fin=date(2026, 9, 1))
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.INVALID_DATE_RANGE)

    def test_invalid_strategy_raises(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(_sample_create(strategy_type="invalid_strategy"))
        self.assertEqual(ctx.exception.code, DomainErrorCode.STRATEGY_TYPE_INVALID)

    def test_r1_single_active_plan(self):
        first = self.service.create_plan(_sample_create())
        second = self.service.create_plan(_sample_create(nombre="Plan alterno Q3"))
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=first.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        with self.assertRaises(DomainError) as ctx:
            self.service.activate_plan(
                ActivatePlanCommand(
                    plan_id=second.plan.id,
                    tenant_id="easytech",
                    activated_by="admin@easytech",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.ACTIVE_PLAN_RESOLUTION_REQUIRED)

    def test_r2_activate_with_finalize_previous(self):
        first = self.service.create_plan(_sample_create())
        second = self.service.create_plan(_sample_create(nombre="Plan alterno Q3"))
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=first.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        result = self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=second.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
                resolution=ConflictResolution.FINALIZE_PREVIOUS,
            )
        )
        self.assertEqual(result.plan.estado, PlanStatus.ACTIVO)
        event_types = [type(e) for e in result.events]
        self.assertIn(PlanCompleted, event_types)
        self.assertIn(PlanActivated, event_types)
        activated = [e for e in result.events if isinstance(e, PlanActivated)][0]
        self.assertEqual(activated.previous_active_plan_id, first.plan.id)
        self.assertEqual(activated.resolution, "finalized_previous")
        self.assertEqual(self.service.get_active_plan("easytech", "en1").id, second.plan.id)

    def test_r2_activate_with_pause_previous(self):
        first = self.service.create_plan(_sample_create())
        second = self.service.create_plan(_sample_create(nombre="Plan alterno Q3"))
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=first.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        result = self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=second.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
                resolution=ConflictResolution.PAUSE_PREVIOUS,
            )
        )
        self.assertEqual(result.plan.estado, PlanStatus.ACTIVO)
        paused = self.service.get_plan(first.plan.id, "easytech")
        self.assertEqual(paused.estado, PlanStatus.PAUSADO)

    def test_idempotent_activate(self):
        created = self.service.create_plan(_sample_create())
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        again = self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        self.assertEqual(again.plan.estado, PlanStatus.ACTIVO)
        self.assertEqual(again.events, [])

    def test_idempotent_pause_and_complete(self):
        created = self.service.create_plan(_sample_create())
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        paused = self.service.pause_plan(
            PausePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                paused_by="admin@easytech",
            )
        )
        again_pause = self.service.pause_plan(
            PausePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                paused_by="admin@easytech",
            )
        )
        self.assertEqual(again_pause.events, [])
        self.assertIsInstance(paused.events[0], PlanPaused)

        completed = self.service.complete_plan(
            CompletePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                completed_by="admin@easytech",
            )
        )
        again_complete = self.service.complete_plan(
            CompletePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                completed_by="admin@easytech",
            )
        )
        self.assertEqual(again_complete.events, [])
        self.assertIsInstance(completed.events[0], PlanCompleted)

    def test_invalid_transition_from_borrador_to_pausado(self):
        created = self.service.create_plan(_sample_create())
        with self.assertRaises(DomainError) as ctx:
            self.service.pause_plan(
                PausePlanCommand(
                    plan_id=created.plan.id,
                    tenant_id="easytech",
                    paused_by="admin@easytech",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.INVALID_STATUS_TRANSITION)

    def test_cannot_update_active_plan(self):
        created = self.service.create_plan(_sample_create())
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        with self.assertRaises(DomainError) as ctx:
            self.service.update_plan(
                UpdatePlanCommand(
                    plan_id=created.plan.id,
                    tenant_id="easytech",
                    updated_by="admin@easytech",
                    nombre="Nombre nuevo",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.PLAN_NOT_EDITABLE)

    def test_update_pausado_plan(self):
        created = self.service.create_plan(_sample_create())
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        self.service.pause_plan(
            PausePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                paused_by="admin@easytech",
            )
        )
        updated = self.service.update_plan(
            UpdatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                updated_by="admin@easytech",
                nombre="Plan revisado Q3",
            )
        )
        self.assertEqual(updated.plan.nombre, "Plan revisado Q3")

    def test_plan_not_found_wrong_tenant(self):
        created = self.service.create_plan(_sample_create())
        with self.assertRaises(DomainError) as ctx:
            self.service.get_plan(created.plan.id, "other_tenant")
        self.assertEqual(ctx.exception.code, DomainErrorCode.PLAN_NOT_FOUND)

    def test_determinism_same_inputs_same_output(self):
        def run_once():
            repo = self.build_repository()
            clock = FixedClock(datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc))
            ids = FixedIdGenerator(plan_ids=["mpl_x"], event_ids=["evt_x"])
            svc = MarketingPlanDomainService(repository=repo, clock=clock, id_generator=ids)
            result = svc.create_plan(_sample_create())
            return result.plan, result.events

        plan_a, events_a = run_once()
        plan_b, events_b = run_once()
        self.assertEqual(plan_a.id, plan_b.id)
        self.assertEqual(plan_a.estado, plan_b.estado)
        self.assertEqual(plan_a.nombre, plan_b.nombre)
        self.assertEqual(len(events_a), len(events_b))
        self.assertEqual(events_a[0].event_id, events_b[0].event_id)

    def test_list_plans_filter_by_estado(self):
        a = self.service.create_plan(_sample_create())
        self.service.create_plan(_sample_create(nombre="Otro borrador"))
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=a.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        activos = self.service.list_plans("easytech", app_id="en1", estado=PlanStatus.ACTIVO)
        self.assertEqual(len(activos), 1)
        borradores = self.service.list_plans("easytech", app_id="en1", estado=PlanStatus.BORRADOR)
        self.assertEqual(len(borradores), 1)

    def test_r3_not_declarative_raises(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(
                _sample_create(
                    objetivo_general="Publicar contenido y programar encolado semanal en redes",
                    marketing_brief="Ejecutar campañas operativas con cron diario para publicar posts.",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.PLAN_NOT_DECLARATIVE)

    def test_r9_forbidden_field_on_create(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(_sample_create(extra_fields={"prompt": "system"}))
        self.assertEqual(ctx.exception.code, DomainErrorCode.FORBIDDEN_FIELD)

    def test_r9_forbidden_field_on_update(self):
        created = self.service.create_plan(_sample_create())
        with self.assertRaises(DomainError) as ctx:
            self.service.update_plan(
                UpdatePlanCommand(
                    plan_id=created.plan.id,
                    tenant_id="easytech",
                    updated_by="admin@easytech",
                    extra_fields={"provider": "openai"},
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.FORBIDDEN_FIELD)

    def test_budget_negative_raises(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(_sample_create(budget_amount=Decimal("-100")))
        self.assertEqual(ctx.exception.code, DomainErrorCode.BUDGET_INVALID)

    def test_currency_invalid_raises(self):
        with self.assertRaises(DomainError) as ctx:
            self.service.create_plan(_sample_create(budget_currency="US"))
        self.assertEqual(ctx.exception.code, DomainErrorCode.CURRENCY_INVALID)

    def test_complete_from_borrador_raises(self):
        created = self.service.create_plan(_sample_create())
        with self.assertRaises(DomainError) as ctx:
            self.service.complete_plan(
                CompletePlanCommand(
                    plan_id=created.plan.id,
                    tenant_id="easytech",
                    completed_by="admin@easytech",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.INVALID_STATUS_TRANSITION)

    def test_update_finalizado_raises(self):
        created = self.service.create_plan(_sample_create())
        self.service.activate_plan(
            ActivatePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                activated_by="admin@easytech",
            )
        )
        self.service.complete_plan(
            CompletePlanCommand(
                plan_id=created.plan.id,
                tenant_id="easytech",
                completed_by="admin@easytech",
            )
        )
        with self.assertRaises(DomainError) as ctx:
            self.service.update_plan(
                UpdatePlanCommand(
                    plan_id=created.plan.id,
                    tenant_id="easytech",
                    updated_by="admin@easytech",
                    nombre="Ya no",
                )
            )
        self.assertEqual(ctx.exception.code, DomainErrorCode.PLAN_COMPLETED)

    def test_tenant_not_found_raises(self):
        class StrictTenantAppValidator:
            def tenant_exists(self, tenant_id: str) -> bool:
                return tenant_id == "easytech"

            def app_exists(self, tenant_id: str, app_id: str) -> bool:
                return tenant_id == "easytech" and app_id == "en1"

        svc = MarketingPlanDomainService(
            repository=self.build_repository(),
            clock=FixedClock(datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)),
            id_generator=FixedIdGenerator(plan_ids=["mpl_t"], event_ids=["evt_t"]),
            tenant_app_validator=StrictTenantAppValidator(),
        )
        with self.assertRaises(DomainError) as ctx:
            svc.create_plan(_sample_create(tenant_id="unknown"))
        self.assertEqual(ctx.exception.code, DomainErrorCode.TENANT_NOT_FOUND)


class MarketingPlanDomainServiceJsonTests(MarketingPlanDomainServiceTests):
    def build_repository(self):
        self._tmpdir = tempfile.mkdtemp()
        return JsonMarketingPlanRepository(Path(self._tmpdir))


if __name__ == "__main__":
    unittest.main()
