#!/usr/bin/env bash
# Publica posts Facebook e Instagram si ya llegó su fecha.
set -euo pipefail
cd /opt/easytech_marketing
source venv/bin/activate
python3 Motor_Tecnico/validate_flyers.py
if ! grep -q '^META_PAGE_ACCESS_TOKEN=.\+' .env 2>/dev/null; then
  echo "Meta no configurado — omitiendo (conectar en /meta/)"
  exit 0
fi
LOG_DIR="/opt/easytech_marketing/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/meta_publish-$(date +%Y%m%d-%H%M).log"
{
  echo "=== Meta auto-publish $(date -Iseconds) ==="
  python3 Motor_Tecnico/meta_publisher.py --platform=facebook || true
  python3 Motor_Tecnico/meta_publisher.py --platform=instagram || true
  echo "=== Fin ==="
} >> "$LOG" 2>&1
