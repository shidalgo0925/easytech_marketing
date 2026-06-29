#!/usr/bin/env python3
"""Import business_context.json → company_profiles (M2 migration)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.company_brain_infrastructure.legacy_mapper import legacy_to_brain, read_legacy_json
from Motor_Tecnico.accio_engine.company_brain_infrastructure.sqlite_repository import SqliteCompanyBrainRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import TENANTS_ROOT, load_registry


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> bool:
    profile = read_legacy_json(tenant_id)
    if not profile:
        return False
    brain = legacy_to_brain(tenant_id, profile)
    if dry_run:
        return True
    SqliteCompanyBrainRepository().save(brain)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate business_context.json to company_profiles")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    migrated = 0
    for tenant_id in tenant_ids:
        path = TENANTS_ROOT / tenant_id / "business_context.json"
        if not path.is_file():
            print(f"  {tenant_id}: skip (no file)")
            continue
        ok = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {'would migrate' if args.dry_run else 'migrated' if ok else 'skip'}")
        if ok:
            migrated += 1
    print(f"Total: {migrated}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
