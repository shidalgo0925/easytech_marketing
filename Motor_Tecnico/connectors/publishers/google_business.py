#!/usr/bin/env python3
"""Publicador Google Business Profile — stub (API pendiente Fase D.4b)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from Motor_Tecnico.connectors.stub_runner import run_stub_publisher  # noqa: E402

if __name__ == "__main__":
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    raise SystemExit(run_stub_publisher("google_business", force=force, dry_run=dry_run))
