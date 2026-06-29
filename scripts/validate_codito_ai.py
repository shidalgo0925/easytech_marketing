#!/usr/bin/env python3
"""Valida conectividad ARROZCONPOLLO → LiteLLM (CODITO) para Accio AI Provider Manager."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

from Motor_Tecnico.accio_engine.ai_provider.config import load_config  # noqa: E402
from Motor_Tecnico.accio_engine.ai_provider import litellm as litellm_client  # noqa: E402
from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider  # noqa: E402


def main() -> int:
    cfg = load_config()
    print("=== Accio AI Provider — validación CODITO ===\n")
    print(f"ACCIO_AI_PROVIDER={cfg.provider}")
    print(f"ACCIO_AI_BASE_URL={cfg.base_url or '(vacío)'}")
    print(f"ACCIO_AI_MODEL={cfg.model}")
    print(f"API key configurada: {'sí' if cfg.api_key else 'no'}\n")

    if not cfg.configured:
        print("FAIL: ACCIO_AI_BASE_URL no configurado en .env")
        print("Ejemplo: ACCIO_AI_BASE_URL=http://<CODITO>:4000")
        return 1

    ping = litellm_client.ping(cfg)
    print(f"Ping /v1/models: ok={ping.get('ok')} models={ping.get('model_count', 0)}")
    if ping.get("models"):
        for mid in ping["models"][:10]:
            print(f"  - {mid}")
    if ping.get("error"):
        print(f"  error: {ping['error']}")
    if ping.get("note"):
        print(f"  note: {ping['note']}")

    status = ai_provider.provider_status()
    print(f"\nprovider_status: reachable={status.get('reachable')} configured={status.get('configured')}")

    model = os.getenv("ACCIO_AI_MODEL", cfg.model)
    if ping.get("models") and model not in ping["models"]:
        print(f"\nWARN: modelo configurado «{model}» no está en la lista devuelta por LiteLLM")

    if not ping.get("ok"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
