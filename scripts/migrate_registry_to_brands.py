#!/usr/bin/env python3
"""Import apps/registry.json → brands table (M3 migration)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.brand_infrastructure.legacy_mapper import registry_to_brands
from Motor_Tecnico.accio_engine.brand_infrastructure.sqlite_repository import SqliteBrandRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import load_registry


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    brands = registry_to_brands(tenant_id)
    if not brands:
        return 0
    if dry_run:
        return len(brands)
    SqliteBrandRepository().save_all(tenant_id, brands)
    return len(brands)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate apps registry to brands table")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} brands")
        total += n
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
