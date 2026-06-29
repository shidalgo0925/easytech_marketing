#!/usr/bin/env python3
"""Import assistant_audit.jsonl → memory_events (M1 migration)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from Motor_Tecnico.accio_engine.memory_api.composition import get_memory_domain_service, reset_memory_use_cases
from Motor_Tecnico.accio_engine.memory_infrastructure.marketing_plan_bridge import audit_entry_to_memory
from Motor_Tecnico.accio_engine.platform_infrastructure.db import ensure_schema, get_db_path
from Motor_Tecnico.accio_engine.tenant import TENANTS_ROOT, load_registry


def migrate_tenant(tenant_id: str, *, dry_run: bool = False) -> int:
    audit_path = TENANTS_ROOT / tenant_id / "assistant_audit.jsonl"
    if not audit_path.is_file():
        return 0
    memory = get_memory_domain_service()
    count = 0
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        event = audit_entry_to_memory(tenant_id, entry)
        if dry_run:
            count += 1
            continue
        try:
            memory.record(event)
            count += 1
        except Exception as exc:
            if "UNIQUE constraint" in str(exc):
                continue
            raise
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate assistant audit to Corporate Memory")
    parser.add_argument("--tenant", help="Single tenant id (default: all in registry)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ensure_schema()
    print(f"DB: {get_db_path()}")
    tenant_ids = [args.tenant] if args.tenant else [t["tenant_id"] for t in load_registry().get("tenants", [])]
    total = 0
    for tenant_id in tenant_ids:
        n = migrate_tenant(tenant_id, dry_run=args.dry_run)
        print(f"  {tenant_id}: {n} events")
        total += n
    reset_memory_use_cases()
    print(f"Total: {total}" + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
