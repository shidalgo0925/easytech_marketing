#!/bin/bash
set -euo pipefail
cd /opt/easytech_marketing
source venv/bin/activate
LOG_DIR="/opt/easytech_marketing/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/pipeline-$(date +%Y%m%d-%H%M).log"
exec > >(tee -a "$LOG") 2>&1
echo "=== Pipeline $(date -Iseconds) ==="
python3 Motor_Tecnico/scraper_panama.py
python3 Motor_Tecnico/odoo_sync.py
echo "=== Fin ==="
