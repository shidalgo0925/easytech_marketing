#!/usr/bin/env python3
"""Import content_queue.json → publications table (M4 migration)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.publication_infrastructure.legacy_mapper import queue_to_publications
from Motor_Tecnico.accio_engine.publication_infrastructure.sqlite_repository import SqlitePublicationRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import load_registry, resolve_tenant


def _queue_paths(tenant_id: str) -> list[tuple[str, Path]]:
    """Return (app_id, queue_path) for tenant root and each app."""
    rows: list[tuple[str, Path]] = []
    tenant_root = resolve_tenant(tenant_id).root
    root_queue = tenant_root / "content_queue.json"
    if root_queue.is_file():
        default_id = marketing_app.default_app_id(tenant_id)
        rows.append((default_id, root_queue))

    apps_dir = tenant_root / "apps"
    if apps_dir.is_dir():
        for app_dir in sorted(apps_dir.iterdir()):
            if not app_dir.is_dir():
                continue
            qpath = app_dir / "content_queue.json"
            if qpath.is_file():
                rows.append((app_dir.name, qpath))
    return rows


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    repo = SqlitePublicationRepository()
    total = 0
    for app_id, qpath in _queue_paths(tenant_id):
        try:
            data = json.loads(qpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        pubs = queue_to_publications(tenant_id, app_id, data)
        if not pubs:
            continue
        total += len(pubs)
        if not dry_run:
            repo.save_all_for_tenant(tenant_id, app_id, pubs)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate content queues to publications table")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} publications")
        total += n
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
