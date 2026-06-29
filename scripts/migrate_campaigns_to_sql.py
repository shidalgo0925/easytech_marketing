#!/usr/bin/env python3
"""Import campaigns.json → campaigns table (M7 migration)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine import marketing_app
from Motor_Tecnico.accio_engine.campaign_infrastructure.legacy_mapper import store_to_campaigns
from Motor_Tecnico.accio_engine.campaign_infrastructure.sqlite_repository import SqliteCampaignRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import load_registry, resolve_tenant


def _campaign_files(tenant_id: str) -> list[tuple[str, Path]]:
    rows: list[tuple[str, Path]] = []
    tenant_root = resolve_tenant(tenant_id).root
    root_file = tenant_root / "campaigns.json"
    if root_file.is_file():
        rows.append((marketing_app.default_app_id(tenant_id), root_file))
    apps_dir = tenant_root / "apps"
    if apps_dir.is_dir():
        for app_dir in sorted(apps_dir.iterdir()):
            if not app_dir.is_dir():
                continue
            cpath = app_dir / "campaigns.json"
            if cpath.is_file():
                rows.append((app_dir.name, cpath))
    return rows


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    repo = SqliteCampaignRepository()
    total = 0
    for brand_id, cpath in _campaign_files(tenant_id):
        try:
            data = json.loads(cpath.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        campaigns = store_to_campaigns(tenant_id, brand_id, data)
        if not campaigns:
            continue
        total += len(campaigns)
        if not dry_run:
            repo.save_all_for_brand(tenant_id, brand_id, campaigns)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate campaigns.json to campaigns table")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} campaigns")
        total += n
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
