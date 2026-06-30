"""Configuración del proveedor IA (servidor Accio — no expuesta a EM+Acción UI)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from Motor_Tecnico.accio_engine.ai_provider import openai_client


@dataclass(frozen=True)
class AIProviderConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout_sec: int
    enabled: bool
    openai_fallback: bool

    @property
    def configured(self) -> bool:
        if self.provider == "disabled":
            return False
        if self.provider == "openai":
            return openai_client.openai_configured()
        if self.provider == "litellm":
            return bool(self.base_url)
        return False

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    @property
    def models_url(self) -> str:
        return f"{self.base_url}/v1/models"


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no", "off")


def load_config() -> AIProviderConfig:
    provider = os.getenv("ACCIO_AI_PROVIDER", "litellm").strip().lower() or "litellm"
    base = os.getenv("ACCIO_AI_BASE_URL", "").strip().rstrip("/")
    if not base and provider == "litellm":
        base = os.getenv("LITELLM_BASE_URL", "").strip().rstrip("/")
    model = (
        os.getenv("ACCIO_AI_MODEL", "").strip()
        or os.getenv("AI_MODEL", "").strip()
        or os.getenv("OPENAI_MODEL", "").strip()
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
    enabled = _env_bool("ACCIO_AI_ENABLED", _env_bool("AI_ASSISTANT_ENABLED", True))
    fallback_raw = os.getenv("ACCIO_AI_OPENAI_FALLBACK", "").strip().lower()
    if fallback_raw in ("0", "false", "no", "off"):
        openai_fallback = False
    elif fallback_raw in ("1", "true", "yes", "on"):
        openai_fallback = True
    else:
        openai_fallback = openai_client.openai_configured()
    return AIProviderConfig(
        provider=provider,
        base_url=base,
        model=model,
        api_key=api_key,
        timeout_sec=max(10, timeout),
        enabled=enabled,
        openai_fallback=openai_fallback,
    )
