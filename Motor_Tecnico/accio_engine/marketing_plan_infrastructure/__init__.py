"""Infrastructure Adapters — stubs y adaptadores (Pieza 4)."""

from .json_repository import JsonMarketingPlanRepository
from .memory import FixedClock, FixedIdGenerator, InMemoryMarketingPlanRepository

__all__ = [
    "FixedClock",
    "FixedIdGenerator",
    "InMemoryMarketingPlanRepository",
    "JsonMarketingPlanRepository",
]
