#!/usr/bin/env python3
"""CLI: migrar cola default de un tenant a colas por app."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Motor_Tecnico.accio_engine.queue_migration import migrate_default_queue_to_apps  # noqa: E402
from Motor_Tecnico.publisher_tenant import parse_tenant_arg  # noqa: E402


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    tenant_id = parse_tenant_arg()
    result = migrate_default_queue_to_apps(tenant_id, dry_run=dry_run)
    import json

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
