#!/usr/bin/env python3
"""Publicador Meta Ads — stub (API pendiente Fase D.5b)."""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from Motor_Tecnico.connectors.stub_runner import run_stub_publisher  # noqa: E402

if __name__ == "__main__":
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv
    raise SystemExit(run_stub_publisher("meta_ads", force=force, dry_run=dry_run))
