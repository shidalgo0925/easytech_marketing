"""Application Layer — casos de uso MarketingPlan (sin HTTP)."""

from .context import ApplicationContext
from .errors import ApplicationError, ApplicationErrorCode
from .results import CommandResult
from .use_cases.commands.activate_marketing_plan import ActivateMarketingPlan
from .use_cases.commands.complete_marketing_plan import CompleteMarketingPlan
from .use_cases.commands.create_marketing_plan import CreateMarketingPlan
from .use_cases.commands.pause_marketing_plan import PauseMarketingPlan
from .use_cases.commands.update_marketing_plan import UpdateMarketingPlan
from .use_cases.queries.get_active_marketing_plan import GetActiveMarketingPlan
from .use_cases.queries.get_marketing_plan import GetMarketingPlan
from .use_cases.queries.list_marketing_plans import ListMarketingPlans

__all__ = [
    "ActivateMarketingPlan",
    "ApplicationContext",
    "ApplicationError",
    "ApplicationErrorCode",
    "CommandResult",
    "CompleteMarketingPlan",
    "CreateMarketingPlan",
    "GetActiveMarketingPlan",
    "GetMarketingPlan",
    "ListMarketingPlans",
    "PauseMarketingPlan",
    "UpdateMarketingPlan",
]
