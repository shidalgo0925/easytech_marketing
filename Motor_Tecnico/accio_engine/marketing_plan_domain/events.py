from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Union

from .enums import ConflictResolution, PlanStatus


@dataclass(frozen=True)
class PlanCreated:
    event_id: str
    occurred_at: datetime
    plan_id: str
    tenant_id: str
    app_id: str
    estado: PlanStatus
    created_by: str


@dataclass(frozen=True)
class PlanActivated:
    event_id: str
    occurred_at: datetime
    plan_id: str
    tenant_id: str
    app_id: str
    previous_active_plan_id: str | None
    resolution: Literal["finalized_previous", "paused_previous"] | None
    activated_by: str


@dataclass(frozen=True)
class PlanPaused:
    event_id: str
    occurred_at: datetime
    plan_id: str
    tenant_id: str
    app_id: str
    paused_by: str


@dataclass(frozen=True)
class PlanCompleted:
    event_id: str
    occurred_at: datetime
    plan_id: str
    tenant_id: str
    app_id: str
    completed_by: str


DomainEvent = Union[PlanCreated, PlanActivated, PlanPaused, PlanCompleted]

RESOLUTION_TO_EVENT: dict[ConflictResolution, Literal["finalized_previous", "paused_previous"]] = {
    ConflictResolution.FINALIZE_PREVIOUS: "finalized_previous",
    ConflictResolution.PAUSE_PREVIOUS: "paused_previous",
}
