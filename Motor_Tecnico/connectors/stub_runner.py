#!/usr/bin/env python3
"""Publisher generico para conectores en modo stub (estructura sin API)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.connectors.queue_tools import append_log, load_queue, pick_next_post  # noqa: E402
from Motor_Tecnico.connectors.registry import get_connector, is_configured  # noqa: E402


def run_stub_publisher(
    connector_id: str,
    force: bool = False,
    dry_run: bool = False,
    tenant_id: str | None = None,
    app_id: str | None = None,
) -> int:
    from Motor_Tecnico.accio_engine import marketing_app
    from Motor_Tecnico.accio_engine.editorial import is_publishable
    from Motor_Tecnico.publisher_tenant import parse_app_arg, parse_tenant_arg, queue_path

    tenant_id = tenant_id or parse_tenant_arg()
    app_id = app_id if app_id is not None else parse_app_arg()
    aid = marketing_app.normalize_app_id(app_id or marketing_app.default_app_id(tenant_id))
    connector = get_connector(connector_id, tenant_id)
    if not connector:
        print(f"Conector no encontrado: {connector_id}")
        return 1

    platform = connector["platform"]
    path = queue_path(tenant_id, aid)
    if not path.is_file():
        print(f"No existe cola para tenant={tenant_id} app={aid}")
        return 1
    raw = json.loads(path.read_text(encoding="utf-8"))
    posts = marketing_app.posts_for_app(raw.get("posts", []), aid, tenant_id)
    queue = {**raw, "posts": posts}
    post = pick_next_post(queue, platform, force=force)
    if not post:
        print(f"No hay posts {platform} pendientes listos para publicar.")
        return 0

    print(f"Post seleccionado ({platform}, tenant={tenant_id}, app={aid}): {post['id']} (programado: {post['scheduled_at']})")

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
            "tenant_id": tenant_id,
            "app_id": aid,
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
