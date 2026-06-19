#!/usr/bin/env python3
"""Valida que todos los posts pending tengan flyer en disco."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.flyer_utils import validate_queue_flyers

QUEUE = BASE_DIR / "Marketing" / "content_queue.json"


def main() -> int:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    missing = validate_queue_flyers(queue)
    if not missing:
        pending = sum(1 for p in queue.get("posts", []) if p.get("status") == "pending")
        print(f"OK — {pending} posts pending, todos con flyer en disco.")
        return 0

    print(f"ERROR — {len(missing)} posts pending sin flyer valido:")
    for row in missing:
        print(f"  - {row['id']} ({row.get('platform')}): {row['reason']} — {row.get('flyer', '')}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
