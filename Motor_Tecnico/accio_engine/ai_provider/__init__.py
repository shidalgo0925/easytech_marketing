"""Accio AI Provider Manager — único punto de salida LLM hacia proveedores externos."""

from Motor_Tecnico.accio_engine.ai_provider.manager import (
    ai_enabled,
    chat_completion,
    complete,
    estimate_cost,
    llm_available,
    llm_unavailable_reason,
    provider_status,
    resolve_model,
)
from Motor_Tecnico.accio_engine.ai_provider.types import AICompletionResult

__all__ = [
    "AICompletionResult",
    "ai_enabled",
    "chat_completion",
    "complete",
    "estimate_cost",
    "llm_available",
    "llm_unavailable_reason",
    "provider_status",
    "resolve_model",
]
