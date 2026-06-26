#!/usr/bin/env python3
"""Crea usuario admin por tenant si aún no hay contraseñas (una sola vez)."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import settings_center  # noqa: E402


def main() -> int:
    pwd = os.getenv("ACCIO_ADMIN_PASSWORD", "").strip()
    generated = False
    if not pwd:
        pwd = secrets.token_urlsafe(12)
        generated = True
    created = settings_center.bootstrap_all_tenants(pwd)
    if not created:
        print("Nada que hacer: todos los tenants ya tienen usuarios con contraseña.")
        return 0
    print("Usuarios admin creados para:", ", ".join(created))
    print("  Usuario: admin")
    print("  Email easytech: admin@easytech.services")
    print(f"  Contraseña: {pwd}")
    if generated:
        env_path = BASE / ".env"
        line = f"ACCIO_ADMIN_PASSWORD={pwd}\n"
        if env_path.is_file() and "ACCIO_ADMIN_PASSWORD" not in env_path.read_text():
            with env_path.open("a", encoding="utf-8") as f:
                f.write(line)
            print("  (guardada en .env como ACCIO_ADMIN_PASSWORD)")
        print("  Cambia la contraseña en Configuración → Usuarios después de entrar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
