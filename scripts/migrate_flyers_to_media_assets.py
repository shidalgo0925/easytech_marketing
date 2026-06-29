#!/usr/bin/env python3
"""Import flyers/manifest.json → media_assets table (M8 migration)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.media_asset_infrastructure.json_repository import JsonMediaAssetRepository
from Motor_Tecnico.accio_engine.media_asset_infrastructure.legacy_mapper import manifest_to_assets
from Motor_Tecnico.accio_engine.media_asset_infrastructure.sqlite_repository import SqliteMediaAssetRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import load_registry


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    manifest = JsonMediaAssetRepository().load_manifest(tenant_id)
    assets = manifest_to_assets(tenant_id, manifest)
    if not assets:
        return 0
    if not dry_run:
        SqliteMediaAssetRepository().save_all_for_tenant(tenant_id, assets)
    return len(assets)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate flyers manifest to media_assets table")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} assets")
        total += n
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
