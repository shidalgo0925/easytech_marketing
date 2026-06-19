#!/usr/bin/env python3
"""Publisher generico para conectores en modo stub (estructura sin API)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.connectors.queue_tools import append_log, load_queue, pick_next_post  # noqa: E402
from Motor_Tecnico.connectors.registry import get_connector, is_configured  # noqa: E402


def run_stub_publisher(connector_id: str, force: bool = False, dry_run: bool = False) -> int:
    connector = get_connector(connector_id)
    if not connector:
        print(f"Conector no encontrado: {connector_id}")
        return 1

    platform = connector["platform"]
    queue = load_queue()
    post = pick_next_post(queue, platform, force=force)
    if not post:
        print(f"No hay posts {platform} pendientes listos para publicar.")
        return 0

    print(f"Post seleccionado ({platform}): {post['id']} (programado: {post['scheduled_at']})")

    if connector.get("implementation") == "stub":
        print(f"[STUB] {connector['name']}: estructura lista, API pendiente.")
        print(f"  Docs: {connector.get('docs', 'docs/FASE_D_CONECTORES.md')}")
        missing = [k for k in connector.get("env_required", []) if not __import__("os").getenv(k, "").strip()]
        if missing:
            print(f"  Variables futuras: {', '.join(missing)}")
        if dry_run:
            print("DRY RUN — no se publico nada.")
            print((post.get("text") or "")[:200] + "...")
            return 0
        print("  Activar API en Fase D.xb para publicar de verdad.")
        return 0

    if not is_configured(connector):
        print(f"[{connector['name']}] Falta OAuth / variables de entorno.")
        return 2

    if dry_run:
        print("DRY RUN — no se publico nada.")
        print((post.get("text") or "")[:200] + "...")
        return 0

    append_log(
        connector.get("log_file", f"Marketing/publish_logs/{platform}.json"),
        {
            "id": post["id"],
            "platform": platform,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "remote_post_id": "stub-not-implemented",
            "utm": post.get("utm"),
        },
    )
    return 0


if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else ""
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    raise SystemExit(run_stub_publisher(cid, force=force, dry_run=dry_run))
