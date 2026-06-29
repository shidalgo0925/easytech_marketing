#!/usr/bin/env python3
"""Router unificado de publicacion por conector/canal."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOTOR_DIR = ROOT / "Motor_Tecnico"
VENV_PYTHON = ROOT / "venv" / "bin" / "python3"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Motor_Tecnico.connectors.registry import get_connector  # noqa: E402
from Motor_Tecnico.connectors.stub_runner import run_stub_publisher  # noqa: E402


from Motor_Tecnico.publisher_tenant import parse_app_arg, parse_tenant_arg  # noqa: E402


def publish(connector_id: str, force: bool = False, dry_run: bool = False, tenant_id: str | None = None, app_id: str | None = None) -> int:
    from Motor_Tecnico.accio_engine import marketing_app
    from Motor_Tecnico.publisher_tenant import parse_app_arg

    tenant_id = tenant_id or parse_tenant_arg()
    app_id = app_id if app_id is not None else parse_app_arg()
    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    connector = get_connector(connector_id, tenant_id)
    if not connector:
        print(f"Conector no encontrado: {connector_id}")
        return 1

    if connector.get("implementation") == "stub":
        return run_stub_publisher(connector_id, force=force, dry_run=dry_run, tenant_id=tenant_id, app_id=aid)

    publisher = connector.get("publisher", "")
    if not publisher:
        print(f"Sin publisher para {connector_id}")
        return 1

    script = MOTOR_DIR / publisher if not publisher.startswith("connectors/") else MOTOR_DIR / publisher
    args = [str(VENV_PYTHON), str(script), f"--tenant-id={tenant_id}", f"--app-id={aid}"]
    args.extend(connector.get("publisher_args") or [])
    if force:
        args.append("--force")
    if dry_run:
        args.append("--dry-run")

    proc = subprocess.run(args, cwd=str(ROOT))
    return proc.returncode


def main() -> None:
    connector_id = ""
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    tenant_id = parse_tenant_arg()
    app_id = parse_app_arg()
    for arg in sys.argv[1:]:
        if arg.startswith("--connector="):
            connector_id = arg.split("=", 1)[1].strip()
        elif arg.startswith("--platform="):
            connector_id = arg.split("=", 1)[1].strip()
        elif not arg.startswith("--"):
            connector_id = arg

    if not connector_id:
        print("Uso: channel_publisher.py --connector=linkedin --tenant-id=easytech [--force] [--dry-run]")
        raise SystemExit(1)

    raise SystemExit(publish(connector_id, force=force, dry_run=dry_run, tenant_id=tenant_id, app_id=app_id))


if __name__ == "__main__":
    main()
