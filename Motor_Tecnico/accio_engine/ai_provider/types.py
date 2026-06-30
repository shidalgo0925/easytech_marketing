"""Tipos normalizados del AI Provider Manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AICompletionResult:
    """Respuesta unificada para todo EM+Acción."""

    content: str
    message: dict[str, Any]
    model: str
    provider: str
    usage: dict[str, Any]
    cost: float | None = None
    tool_calls: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "cost": self.cost,
            "tool_calls": self.tool_calls,
        }
