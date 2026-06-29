"""Corporate Memory — infrastructure adapters (M1)."""

from .marketing_plan_bridge import MarketingPlanMemoryEventPublisher
from .sqlite_repository import SqliteMemoryRepository

__all__ = ["MarketingPlanMemoryEventPublisher", "SqliteMemoryRepository"]
