#!/usr/bin/env bash
# Publica el siguiente post LinkedIn si ya llegó su fecha (sin intervención humana).
set -euo pipefail
cd /opt/easytech_marketing
source venv/bin/activate
python3 Motor_Tecnico/validate_flyers.py
LOG_DIR="/opt/easytech_marketing/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/linkedin_publish-$(date +%Y%m%d-%H%M).log"
{
  echo "=== LinkedIn auto-publish $(date -Iseconds) ==="
  python3 Motor_Tecnico/linkedin_publisher.py
  echo "=== Fin ==="
} >> "$LOG" 2>&1
