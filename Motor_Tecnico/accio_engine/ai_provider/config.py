"""Configuración del proveedor IA (servidor Accio — no expuesta a EM+Acción UI)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout_sec: int

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    @property
    def models_url(self) -> str:
        return f"{self.base_url}/v1/models"


def load_config() -> AIProviderConfig:
    provider = os.getenv("ACCIO_AI_PROVIDER", "litellm").strip().lower() or "litellm"
    base = os.getenv("ACCIO_AI_BASE_URL", "").strip().rstrip("/")
    if not base and provider == "litellm":
        # Alias legacy / documentación CODITO
        base = os.getenv("LITELLM_BASE_URL", "").strip().rstrip("/")
    model = (
        os.getenv("ACCIO_AI_MODEL", "").strip()
        or os.getenv("AI_MODEL", "").strip()
        or "qwen2.5-coder:14b"
    )
    api_key = (
        os.getenv("ACCIO_AI_API_KEY", "").strip()
        or os.getenv("LITELLM_API_KEY", "").strip()
    )
    try:
        timeout = int(os.getenv("ACCIO_AI_TIMEOUT", "90"))
    except ValueError:
        timeout = 90
    return AIProviderConfig(
        provider=provider,
        base_url=base,
        model=model,
        api_key=api_key,
        timeout_sec=max(10, timeout),
    )
