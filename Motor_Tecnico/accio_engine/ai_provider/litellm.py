"""Cliente LiteLLM (API compatible OpenAI /v1)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from Motor_Tecnico.accio_engine.ai_provider.config import AIProviderConfig


def _headers(cfg: AIProviderConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    return headers


def chat_completions(
    cfg: AIProviderConfig,
    body: dict[str, Any],
) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        cfg.chat_completions_url,
        data=data,
        headers=_headers(cfg),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"AI provider HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"AI provider unreachable: {exc.reason}") from exc


def list_models(cfg: AIProviderConfig) -> list[dict[str, Any]]:
    req = urllib.request.Request(cfg.models_url, headers=_headers(cfg), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=min(cfg.timeout_sec, 15)) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError):
        return []
    rows = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return []
    return [r for r in rows if isinstance(r, dict)]


def ping(cfg: AIProviderConfig) -> dict[str, Any]:
    if not cfg.configured:
        return {"ok": False, "error": "ACCIO_AI_BASE_URL not configured"}
    models = list_models(cfg)
    if models:
        ids = [str(m.get("id", "")) for m in models if m.get("id")]
        return {"ok": True, "models": ids[:20], "model_count": len(ids)}
    # LiteLLM sin /models o vacío — intentar health implícito vía chat mínimo no vale la pena
    return {"ok": True, "models": [], "model_count": 0, "note": "models endpoint empty or unavailable"}
