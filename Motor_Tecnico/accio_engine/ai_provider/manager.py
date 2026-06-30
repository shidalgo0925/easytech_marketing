"""Accio AI Provider Manager — orquesta proveedores (LiteLLM/CODITO + OpenAI fallback)."""

from __future__ import annotations

import os
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider.config import AIProviderConfig, load_config
from Motor_Tecnico.accio_engine.ai_provider import litellm as litellm_client
from Motor_Tecnico.accio_engine.ai_provider import openai_client
from Motor_Tecnico.accio_engine.ai_provider.types import AICompletionResult

DEFAULT_MODEL = "qwen2.5-coder:14b"
UNAVAILABLE = "AI_PROVIDER_UNAVAILABLE"


def ai_enabled(ai_cfg: dict[str, Any] | None = None) -> bool:
    cfg = load_config()
    if not cfg.enabled:
        return False
    if cfg.provider == "disabled":
        return False
    raw = os.getenv("AI_ASSISTANT_ENABLED", "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    tenant_cfg = ai_cfg or {}
    return tenant_cfg.get("enabled", True) is not False


def assistant_enabled(ai_cfg: dict[str, Any] | None = None) -> bool:
    return ai_enabled(ai_cfg)


def resolve_model(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> str:
    _ = tenant_id
    env_model = os.getenv("ACCIO_AI_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "").strip()
    if env_model:
        return env_model
    cfg = ai_cfg or {}
    return (cfg.get("model") or cfg.get("openai_model") or load_config().model or DEFAULT_MODEL).strip()


def llm_available(tenant_id: str, ai_cfg: dict[str, Any] | None = None) -> bool:
    _ = tenant_id
    if not ai_enabled(ai_cfg):
        return False
    cfg = load_config()
    if cfg.provider == "disabled":
        return False
    if cfg.provider == "openai":
        return openai_client.openai_configured()
    if cfg.configured:
        return True
    return cfg.openai_fallback and openai_client.openai_configured()


def llm_unavailable_reason(ai_cfg: dict[str, Any] | None = None) -> str | None:
    if llm_available("system", ai_cfg):
        return None
    cfg = load_config()
    if not cfg.enabled:
        return "ACCIO_AI_ENABLED=false"
    if cfg.provider == "disabled":
        return "ACCIO_AI_PROVIDER=disabled"
    if not ai_enabled(ai_cfg):
        return "assistant_disabled"
    if cfg.provider == "litellm" and not cfg.configured and not (cfg.openai_fallback and openai_client.openai_configured()):
        return "ACCIO_AI_BASE_URL not configured"
    if cfg.provider == "openai" and not openai_client.openai_configured():
        return "OPENAI_API_KEY not configured"
    return "provider_unreachable"


def provider_status() -> dict[str, Any]:
    cfg = load_config()
    out: dict[str, Any] = {
        "provider": cfg.provider,
        "base_url": cfg.base_url or None,
        "model": resolve_model("system"),
        "configured": cfg.configured,
        "enabled": cfg.enabled,
        "assistant_enabled": ai_enabled(),
        "openai_fallback": cfg.openai_fallback,
        "openai_configured": openai_client.openai_configured(),
        "unavailable_reason": llm_unavailable_reason(),
    }
    if cfg.provider == "litellm" and cfg.configured:
        ping = litellm_client.ping(cfg)
        out["reachable"] = ping.get("ok", False)
        out["models"] = ping.get("models", [])
        if ping.get("error"):
            out["error"] = ping["error"]
    elif cfg.provider == "openai" and openai_client.openai_configured():
        out["reachable"] = True
        out["active_provider"] = "openai"
    else:
        out["reachable"] = bool(out.get("openai_configured")) if cfg.openai_fallback else False
    if llm_available("system"):
        out["active_provider"] = "openai" if cfg.provider == "openai" else (
            "litellm" if cfg.configured else "openai"
        )
    return out


def estimate_cost(usage: dict[str, Any]) -> float | None:
    if not usage:
        return None
    return round(
        usage.get("prompt_tokens", 0) * 0.00000015 + usage.get("completion_tokens", 0) * 0.0000006,
        4,
    )


def _message_content(msg: dict[str, Any]) -> str:
    return str(msg.get("content") or "").strip()


def _litellm_complete(cfg: AIProviderConfig, body: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    data = litellm_client.chat_completions(cfg, body)
    msg = data["choices"][0]["message"]
    usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
    model_name = str(data.get("model") or body.get("model") or cfg.model)
    return msg, model_name, usage, "litellm"


def _openai_complete(cfg: AIProviderConfig, body: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any], str]:
    api_key = openai_client.resolve_openai_api_key()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    data = openai_client.chat_completions(api_key=api_key, body=body, timeout_sec=cfg.timeout_sec)
    msg = data["choices"][0]["message"]
    usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
    model_name = str(data.get("model") or body.get("model") or resolve_model("system"))
    return msg, model_name, usage, "openai"


def complete(
    tenant_id: str,
    messages: list[dict[str, Any]],
    *,
    model: str | None = None,
    ai_cfg: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.65,
) -> AICompletionResult:
    if not llm_available(tenant_id, ai_cfg):
        reason = llm_unavailable_reason(ai_cfg) or UNAVAILABLE
        raise RuntimeError(f"{UNAVAILABLE}: {reason}")

    cfg = load_config()
    model_name = model or resolve_model(tenant_id, ai_cfg)
    body: dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    errors: list[str] = []
    if cfg.provider == "openai":
        try:
            msg, used_model, usage, provider = _openai_complete(cfg, body)
            return AICompletionResult(
                content=_message_content(msg),
                message=msg,
                model=used_model,
                provider=provider,
                usage=usage,
                cost=estimate_cost(usage),
                tool_calls=msg.get("tool_calls"),
            )
        except RuntimeError as exc:
            raise RuntimeError(f"{UNAVAILABLE}: {exc}") from exc

    if cfg.provider == "litellm" and cfg.configured:
        try:
            msg, used_model, usage, provider = _litellm_complete(cfg, body)
            return AICompletionResult(
                content=_message_content(msg),
                message=msg,
                model=used_model,
                provider=provider,
                usage=usage,
                cost=estimate_cost(usage),
                tool_calls=msg.get("tool_calls"),
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    if cfg.openai_fallback and openai_client.openai_configured():
        try:
            msg, used_model, usage, provider = _openai_complete(cfg, body)
            return AICompletionResult(
                content=_message_content(msg),
                message=msg,
                model=used_model,
                provider=provider,
                usage=usage,
                cost=estimate_cost(usage),
                tool_calls=msg.get("tool_calls"),
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    detail = "; ".join(errors) if errors else (llm_unavailable_reason(ai_cfg) or "unknown")
    raise RuntimeError(f"{UNAVAILABLE}: {detail}")


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
    result = complete(
        tenant_id,
        messages,
        model=model,
        ai_cfg=ai_cfg,
        tools=tools,
        temperature=temperature,
    )
    return result.message, result.model, result.cost
