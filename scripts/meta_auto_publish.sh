#!/usr/bin/env bash
# Publica posts Facebook e Instagram si ya llegó su fecha.
set -euo pipefail
cd /opt/easytech_marketing
source venv/bin/activate
LOG_DIR="/opt/easytech_marketing/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/meta_publish-$(date +%Y%m%d-%H%M).log"
{
  echo "=== Meta auto-publish $(date -Iseconds) ==="
  python3 Motor_Tecnico/meta_publisher.py --platform=facebook || true
  python3 Motor_Tecnico/meta_publisher.py --platform=instagram || true
  echo "=== Fin ==="
} >> "$LOG" 2>&1
