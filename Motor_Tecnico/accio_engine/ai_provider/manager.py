"""Accio AI Provider Manager — orquesta proveedores (V1: LiteLLM → Ollama en CODITO)."""

from __future__ import annotations

import os
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider.config import AIProviderConfig, load_config
from Motor_Tecnico.accio_engine.ai_provider import litellm as litellm_client

DEFAULT_MODEL = "qwen2.5-coder:14b"


def assistant_enabled(ai_cfg: dict[str, Any] | None = None) -> bool:
    raw = os.getenv("AI_ASSISTANT_ENABLED", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    cfg = ai_cfg or {}
    return cfg.get("enabled", True) is not False


def resolve_model(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> str:
    _ = tenant_id
    env_model = os.getenv("ACCIO_AI_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "").strip()
    if env_model:
        return env_model
    cfg = ai_cfg or {}
    return (cfg.get("model") or cfg.get("openai_model") or load_config().model or DEFAULT_MODEL).strip()


def llm_available(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> bool:
    _ = tenant_id
    if not assistant_enabled(ai_cfg):
        return False
    return load_config().configured


def provider_status() -> dict[str, Any]:
    cfg = load_config()
    out: dict[str, Any] = {
        "provider": cfg.provider,
        "base_url": cfg.base_url or None,
        "model": resolve_model("system"),
        "configured": cfg.configured,
        "assistant_enabled": assistant_enabled(),
    }
    if cfg.configured and cfg.provider == "litellm":
        ping = litellm_client.ping(cfg)
        out["reachable"] = ping.get("ok", False)
        out["models"] = ping.get("models", [])
        if ping.get("error"):
            out["error"] = ping["error"]
    else:
        out["reachable"] = False
    return out


def estimate_cost(usage: dict[str, Any]) -> float | None:
    if not usage:
        return None
    return round(
        usage.get("prompt_tokens", 0) * 0.00000015 + usage.get("completion_tokens", 0) * 0.0000006,
        4,
    )


def chat_completion(
    tenant_id: str,
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    ai_cfg: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.65,
) -> tuple[dict[str, Any], str, float | None]:
    """Returns (message_dict, model_name, cost). message may include tool_calls."""
    _ = tenant_id
    if not llm_available(tenant_id, ai_cfg):
        raise RuntimeError("AI_PROVIDER_UNAVAILABLE")

    cfg = load_config()
    if cfg.provider != "litellm":
        raise RuntimeError(f"AI provider not supported: {cfg.provider}")

    model_name = model or resolve_model(tenant_id, ai_cfg)
    body: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    data = litellm_client.chat_completions(cfg, body)
    msg = data["choices"][0]["message"]
    return msg, model_name, estimate_cost(data.get("usage", {}))
