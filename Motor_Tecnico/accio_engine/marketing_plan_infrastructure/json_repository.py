"""JSON Repository Adapter — implementa MarketingPlanRepository."""

from __future__ import annotations

from pathlib import Path

from Motor_Tecnico.accio_engine.marketing_plan_domain.enums import PlanStatus
from Motor_Tecnico.accio_engine.marketing_plan_domain.model import MarketingPlan

from .mapper import plan_to_record, record_to_plan
from .serializer import read_record, write_record


class JsonMarketingPlanRepository:
    """Traduce MarketingPlan ↔ JSON en filesystem. Solo consultas del puerto."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def get_by_id(self, plan_id: str) -> MarketingPlan | None:
        path = self._locate_plan_path(plan_id)
        if path is None:
            return None
        return record_to_plan(read_record(path)).copy()

    def save(self, plan: MarketingPlan) -> None:
        path = self._plan_path(plan.tenant_id, plan.app_id, plan.id)
        write_record(path, plan_to_record(plan))

    def find_active(self, tenant_id: str, app_id: str) -> MarketingPlan | None:
        for plan in self._iter_plans(tenant_id, app_id):
            if plan.estado == PlanStatus.ACTIVO:
                return plan.copy()
        return None

    def list_plans(
        self,
        tenant_id: str,
        *,
        app_id: str | None = None,
        estado: PlanStatus | None = None,
    ) -> list[MarketingPlan]:
        rows: list[MarketingPlan] = []
        if app_id is not None:
            candidates = self._iter_plans(tenant_id, app_id)
        else:
            candidates = self._iter_tenant_plans(tenant_id)
        for plan in candidates:
            if estado is not None and plan.estado != estado:
                continue
            rows.append(plan.copy())
        rows.sort(key=lambda p: p.created_at)
        return rows

    def _plan_path(self, tenant_id: str, app_id: str, plan_id: str) -> Path:
        return (
            self._root
            / tenant_id
            / "apps"
            / app_id
            / "marketing_plans"
            / f"{plan_id}.json"
        )

    def _plans_dir(self, tenant_id: str, app_id: str) -> Path:
        return self._root / tenant_id / "apps" / app_id / "marketing_plans"

    def _locate_plan_path(self, plan_id: str) -> Path | None:
        pattern = f"{plan_id}.json"
        matches = sorted(self._root.rglob(pattern))
        scoped = [p for p in matches if p.parent.name == "marketing_plans"]
        if not scoped:
            return None
        return scoped[0]

    def _iter_plans(self, tenant_id: str, app_id: str) -> list[MarketingPlan]:
        directory = self._plans_dir(tenant_id, app_id)
        if not directory.is_dir():
            return []
        rows: list[MarketingPlan] = []
        for path in sorted(directory.glob("*.json")):
            rows.append(record_to_plan(read_record(path)))
        return rows

    def _iter_tenant_plans(self, tenant_id: str) -> list[MarketingPlan]:
        rows: list[MarketingPlan] = []
        apps_root = self._root / tenant_id / "apps"
        if not apps_root.is_dir():
            return rows
        for app_dir in sorted(apps_root.iterdir()):
            if not app_dir.is_dir():
                continue
            rows.extend(self._iter_plans(tenant_id, app_dir.name))
        return rows
