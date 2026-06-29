#!/usr/bin/env python3
"""Tests Application Layer — casos de uso sin HTTP."""

from __future__ import annotations

import sys
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.marketing_plan_application.adapters import (  # noqa: E402
    AllowAllAuthorization,
    CollectingDomainEventPublisher,
    NoOpWorkspace,
    RoleBasedAuthorization,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.command_inputs import (  # noqa: E402
    ActivateMarketingPlanInput,
    CreateMarketingPlanInput,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.context import ApplicationContext  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_application.errors import (  # noqa: E402
    ApplicationError,
    ApplicationErrorCode,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.query_inputs import (  # noqa: E402
    GetActiveMarketingPlanQuery,
    ListMarketingPlansQuery,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.commands.create_marketing_plan import (  # noqa: E402
    CreateMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.commands.activate_marketing_plan import (  # noqa: E402
    ActivateMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.queries.get_active_marketing_plan import (  # noqa: E402
    GetActiveMarketingPlan,
)
from Motor_Tecnico.accio_engine.marketing_plan_application.use_cases.queries.list_marketing_plans import (  # noqa: E402
    ListMarketingPlans,
)
from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import PlanStatus  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_domain.errors import DomainErrorCode  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_domain.events import PlanCreated  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_domain.service import MarketingPlanDomainService  # noqa: E402
from Motor_Tecnico.accio_engine.marketing_plan_infrastructure.memory import (  # noqa: E402
    FixedClock,
    FixedIdGenerator,
    InMemoryMarketingPlanRepository,
)


def _ctx(role: str = "admin") -> ApplicationContext:
    return ApplicationContext(
        tenant_id="easytech",
        app_id="en1",
        actor_id="admin@easytech",
        actor_role=role,
    )


def _sample_input() -> CreateMarketingPlanInput:
    return CreateMarketingPlanInput(
        nombre="Plan Q3 EN1",
        objetivo_general="Incrementar leads cualificados en el segmento PYME",
        strategy_type="lead_generation",
        north_star_metric="Leads cualificados mensuales",
        success_criteria=["100 leads", "20 reuniones"],
        publico_objetivo=["Gerentes PYME", "Contadores"],
        marketing_brief=(
            "Enfoque en propuesta de valor EN1, competencia local, "
            "dolores de facturación y restricciones de presupuesto."
        ),
        periodo_inicio=date(2026, 7, 1),
        periodo_fin=date(2026, 9, 30),
        budget_amount=Decimal("5000"),
        budget_currency="USD",
        prioridad="alta",
    )


class ApplicationLayerTests(unittest.TestCase):
    def setUp(self):
        self.events = CollectingDomainEventPublisher()
        self.domain = MarketingPlanDomainService(
            repository=InMemoryMarketingPlanRepository(),
            clock=FixedClock(datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)),
            id_generator=FixedIdGenerator(plan_ids=["mpl_app_1", "mpl_app_2"], event_ids=["evt_a1", "evt_a2"]),
        )
        self.workspace = NoOpWorkspace()
        self.auth = AllowAllAuthorization()

    def test_create_marketing_plan_publishes_events(self):
        use_case = CreateMarketingPlan(self.domain, self.auth, self.workspace, self.events)
        result = use_case(_ctx(), _sample_input())
        self.assertEqual(result.plan.id, "mpl_app_1")
        self.assertEqual(len(self.events.published), 1)
        self.assertIsInstance(self.events.published[0], PlanCreated)

    def test_create_forbidden_without_config_or_admin(self):
        auth = RoleBasedAuthorization({"viewer": {"read"}})
        use_case = CreateMarketingPlan(self.domain, auth, self.workspace, self.events)
        with self.assertRaises(ApplicationError) as ctx:
            use_case(_ctx(role="viewer"), _sample_input())
        self.assertEqual(ctx.exception.code, ApplicationErrorCode.FORBIDDEN)
        self.assertEqual(len(self.events.published), 0)

    def test_query_does_not_publish_events(self):
        create = CreateMarketingPlan(self.domain, self.auth, self.workspace, self.events)
        created = create(_ctx(), _sample_input())
        self.events.published.clear()

        activate = ActivateMarketingPlan(self.domain, self.auth, self.workspace, self.events)
        activate(_ctx(), ActivateMarketingPlanInput(plan_id=created.plan.id))
        events_after_activate = len(self.events.published)

        get_active = GetActiveMarketingPlan(self.domain, self.auth, self.workspace)
        plan = get_active(_ctx(), GetActiveMarketingPlanQuery())
        self.assertIsNotNone(plan)
        self.assertEqual(len(self.events.published), events_after_activate)

    def test_list_marketing_plans_read_only(self):
        create = CreateMarketingPlan(self.domain, self.auth, self.workspace, self.events)
        create(_ctx(), _sample_input())
        self.events.published.clear()

        list_plans = ListMarketingPlans(self.domain, self.auth, self.workspace)
        rows = list_plans(_ctx(role="viewer"), ListMarketingPlansQuery())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].estado, PlanStatus.BORRADOR)
        self.assertEqual(len(self.events.published), 0)

    def test_domain_error_wrapped_not_swallowed(self):
        use_case = CreateMarketingPlan(self.domain, self.auth, self.workspace, self.events)
        base = _sample_input()
        bad = CreateMarketingPlanInput(
            nombre=base.nombre,
            objetivo_general=base.objetivo_general,
            strategy_type=base.strategy_type,
            north_star_metric=base.north_star_metric,
            success_criteria=base.success_criteria,
            publico_objetivo=base.publico_objetivo,
            marketing_brief=base.marketing_brief,
            periodo_inicio=date(2026, 10, 1),
            periodo_fin=date(2026, 9, 1),
            budget_amount=base.budget_amount,
            budget_currency=base.budget_currency,
            prioridad=base.prioridad,
        )
        with self.assertRaises(ApplicationError) as ctx:
            use_case(_ctx(), bad)
        self.assertEqual(ctx.exception.source, "domain")
        assert ctx.exception.domain_error is not None
        self.assertEqual(ctx.exception.domain_error.code, DomainErrorCode.INVALID_DATE_RANGE)


if __name__ == "__main__":
    unittest.main()
