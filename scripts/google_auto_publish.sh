#!/usr/bin/env bash
# Publica Google Business Profile si hay post listo.
set -euo pipefail
cd /opt/easytech_marketing
source venv/bin/activate
python3 Motor_Tecnico/validate_flyers.py
LOG_DIR="/opt/easytech_marketing/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/google_publish-$(date +%Y%m%d-%H%M).log"
{
  echo "=== Google Business auto-publish $(date -Iseconds) ==="
  python3 Motor_Tecnico/channel_publisher.py --connector=google_business || true
  echo "=== Fin ==="
} >> "$LOG" 2>&1
