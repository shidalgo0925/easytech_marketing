#!/usr/bin/env python3
"""Import products.json → products table (M5 migration)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.product_infrastructure.legacy_mapper import catalog_to_products
from Motor_Tecnico.accio_engine.product_infrastructure.sqlite_repository import SqliteProductRepository
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import load_registry, resolve_tenant


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    path = resolve_tenant(tenant_id).root / "products.json"
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    products = catalog_to_products(tenant_id, data)
    if not products:
        return 0
    if not dry_run:
        SqliteProductRepository().save_all_for_tenant(tenant_id, products)
    return len(products)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate products.json to products table")
    parser.add_argument("--tenant", help="Single tenant id")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} products")
        total += n
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
