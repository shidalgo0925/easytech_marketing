#!/usr/bin/env python3
"""Verificación Bloque 2 — AI Provider + enrich disponible."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

from Motor_Tecnico.accio_engine.ai_provider import manager as ai_provider  # noqa: E402
from Motor_Tecnico.accio_engine.ai_provider.config import load_config  # noqa: E402


def main() -> int:
    errors: list[str] = []
    cfg = load_config()

    print("=== Bloque 2 — IA prod ===\n")
    print(f"provider={cfg.provider} enabled={cfg.enabled}")
    print(f"base_url={cfg.base_url or '(vacío)'}")
    print(f"model={cfg.model}")

    if not cfg.configured:
        errors.append("ACCIO_AI_BASE_URL no configurado — ejecutar enable_ai_prod.sh con CODITO_HOST")

    status = ai_provider.provider_status()
    print(f"\nprovider_status: reachable={status.get('reachable')} reason={status.get('unavailable_reason')}")

    if not ai_provider.llm_available("easytech"):
        errors.append(f"llm_available=false ({status.get('unavailable_reason')})")
    elif cfg.provider == "litellm" and not status.get("reachable"):
        errors.append("LiteLLM configurado pero no responde (red/firewall/DNS)")

    if ai_provider.llm_available("easytech") and cfg.configured:
        try:
            msg, model, _cost = ai_provider.chat_completion(
                "easytech",
                [
                    {"role": "system", "content": "Responde solo JSON: {\"ok\": true}"},
                    {"role": "user", "content": "ping"},
                ],
                temperature=0,
            )
            content = (msg.get("content") or "").strip()
            print(f"\nSmoke chat: model={model} len={len(content)}")
            if not content:
                errors.append("chat completion vacío")
        except Exception as exc:
            errors.append(f"chat completion falló: {exc}")

    env_prod = BASE / "deploy" / "secrets" / ".env.prod"
    if env_prod.is_file():
        text = env_prod.read_text(encoding="utf-8")
        if "ACCIO_AI_BASE_URL" not in text and not cfg.base_url:
            print("\nNota: añadir ACCIO_AI_BASE_URL a deploy/secrets/.env.prod (opcional)")

    if errors:
        print("\nFALLOS:")
        for e in errors:
            print(f"  - {e}")
        print("\nVer docs/BLOQUE2_IA_PROD.md y docs/CONECTAR_CODITO.md")
        return 1

    print("\nOK — Bloque 2 verificación pasada (IA operativa).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
