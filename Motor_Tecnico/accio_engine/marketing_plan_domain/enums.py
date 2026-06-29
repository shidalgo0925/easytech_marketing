from __future__ import annotations

from enum import Enum


class StrategyType(str, Enum):
    LEAD_GENERATION = "lead_generation"
    BRAND_AWARENESS = "brand_awareness"
    REMARKETING = "remarketing"
    LAUNCH = "launch"
    UPSELLING = "upselling"
    CROSS_SELLING = "cross_selling"
    RETENTION = "retention"


class PlanStatus(str, Enum):
    BORRADOR = "borrador"
    ACTIVO = "activo"
    PAUSADO = "pausado"
    FINALIZADO = "finalizado"


class PlanPriority(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class ConflictResolution(str, Enum):
    FINALIZE_PREVIOUS = "finalize_previous"
    PAUSE_PREVIOUS = "pause_previous"


ALLOWED_TRANSITIONS: dict[PlanStatus, frozenset[PlanStatus]] = {
    PlanStatus.BORRADOR: frozenset({PlanStatus.ACTIVO}),
    PlanStatus.ACTIVO: frozenset({PlanStatus.PAUSADO, PlanStatus.FINALIZADO}),
    PlanStatus.PAUSADO: frozenset({PlanStatus.ACTIVO, PlanStatus.FINALIZADO}),
    PlanStatus.FINALIZADO: frozenset(),
}
