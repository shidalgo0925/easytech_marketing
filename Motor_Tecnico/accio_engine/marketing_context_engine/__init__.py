"""Marketing Context Engine — fuente única de contexto para IA y módulos."""

from Motor_Tecnico.accio_engine.marketing_context_engine.builder import (
    MarketingContextBuilder,
    get_marketing_context_builder,
    reset_marketing_context_builder,
)
from Motor_Tecnico.accio_engine.marketing_context_engine.constants import (
    COMMERCIAL_CTA,
    COMMERCIAL_GUIDE_URL,
    EDITORIAL_RULE_LABEL,
)

__all__ = [
    "COMMERCIAL_CTA",
    "COMMERCIAL_GUIDE_URL",
    "EDITORIAL_RULE_LABEL",
    "MarketingContextBuilder",
    "get_marketing_context_builder",
    "reset_marketing_context_builder",
]
