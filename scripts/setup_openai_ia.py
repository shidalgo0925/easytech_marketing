#!/usr/bin/env python3
"""Configura IA (OpenAI) para todos los tenants EM+Acción.

Uso (elige uno):
  OPENAI_API_KEY=sk-… python3 scripts/setup_openai_ia.py
  python3 scripts/setup_openai_ia.py --from-file deploy/secrets/openai.key
  echo 'sk-…' > deploy/secrets/openai.key && chmod 600 deploy/secrets/openai.key && python3 scripts/setup_openai_ia.py --from-file deploy/secrets/openai.key
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.env_loader import load_accio_env  # noqa: E402

load_accio_env(BASE)

from Motor_Tecnico.accio_engine import assistant_llm, settings_center, tenant_secrets  # noqa: E402
from Motor_Tecnico.accio_engine.tenant import list_tenants  # noqa: E402


def _read_key(from_file: str | None) -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key and from_file:
        path = Path(from_file)
        if not path.is_absolute():
            path = BASE / path
        if path.is_file():
            key = path.read_text(encoding="utf-8").strip()
    if not key:
        print("ERROR: Falta OPENAI_API_KEY (env o --from-file).", file=sys.stderr)
        sys.exit(1)
    if not re.match(r"^sk-[A-Za-z0-9_-]{8,}", key):
        print("ERROR: La clave no parece una OpenAI API Key válida (sk-…).", file=sys.stderr)
        sys.exit(1)
    return key


def _upsert_env_line(path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    found = False
    if path.is_file():
        lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _ensure_ai_json(tenant_id: str) -> None:
    path = BASE / "Marketing" / "tenants" / tenant_id / "ai.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {
            "topic_model": "llm",
            "image_model": "static_flyers",
            "tone_override": "",
            "enabled": True,
        }
    data["enabled"] = True
    data["topic_model"] = data.get("topic_model") or "llm"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tenant_ids() -> list[str]:
    try:
        return [t.tenant_id for t in list_tenants(active_only=True)]
    except Exception:
        return ["easytech", "relatic"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Configurar OpenAI IA en EM+Acción")
    parser.add_argument("--from-file", help="Archivo con la API key (una línea)")
    parser.add_argument("--no-restart", action="store_true", help="No reiniciar systemd")
    args = parser.parse_args()

    api_key = _read_key(args.from_file)

    env_path = BASE / ".env"
    secrets_prod = BASE / "deploy" / "secrets" / ".env.prod"
    secrets_prod.parent.mkdir(parents=True, exist_ok=True)

    _upsert_env_line(env_path, "OPENAI_API_KEY", api_key)
    _upsert_env_line(env_path, "AI_ASSISTANT_ENABLED", "true")
    _upsert_env_line(env_path, "OPENAI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    _upsert_env_line(secrets_prod, "OPENAI_API_KEY", api_key)
    _upsert_env_line(secrets_prod, "AI_ASSISTANT_ENABLED", "true")
    _upsert_env_line(secrets_prod, "OPENAI_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    tenants = _tenant_ids()
    for tid in tenants:
        tenant_secrets.set_secret(tid, "variables", "openai_api_key", api_key, actor="setup_openai_ia")
        _ensure_ai_json(tid)
        cfg = settings_center.load_ai_config(tid)
        settings_center.save_ai_config(tid, {"enabled": True, "topic_model": "llm"})
        ok = assistant_llm.llm_available(tid, cfg)
        print(f"  {tid}: openai guardada · llm_available={ok}")

    if not args.no_restart:
        try:
            subprocess.run(
                ["sudo", "systemctl", "restart", "easytech-accio-engine"],
                check=True,
                timeout=30,
            )
            print("  servicio: easytech-accio-engine reiniciado")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"  aviso: no se pudo reiniciar servicio ({exc}). Ejecuta: sudo systemctl restart easytech-accio-engine")

    print("\n✅ IA configurada. Verifica en /accio/plan/{tenant}/ → topbar «IA activa».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
