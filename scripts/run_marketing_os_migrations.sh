#!/usr/bin/env bash
# Orquestador M1–M9: JSON legacy → marketing_os.db (Bloque 1)
set -euo pipefail

ROOT="${ACCIO_ROOT:-/opt/easytech_marketing}"
cd "$ROOT"

export ACCIO_PLATFORM_DB="${ACCIO_PLATFORM_DB:-$ROOT/Marketing/platform/marketing_os.db}"
PYTHON="${ROOT}/venv/bin/python3"

DRY=0
TENANT_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --tenant) TENANT_ARGS=(--tenant "$2"); shift 2 ;;
    *) echo "Uso: $0 [--dry-run] [--tenant ID]"; exit 1 ;;
  esac
done

SCRIPTS=(
  migrate_audit_to_memory
  migrate_business_context_to_brain
  migrate_registry_to_brands
  migrate_content_queue_to_publications
  migrate_products_to_sql
  migrate_knowledge_to_sql
  migrate_campaigns_to_sql
  migrate_flyers_to_media_assets
  migrate_leads_to_sql
)

echo "ACCIO_PLATFORM_DB=$ACCIO_PLATFORM_DB"
if [[ "$DRY" -eq 1 ]]; then
  echo "=== DRY RUN ==="
fi

for script in "${SCRIPTS[@]}"; do
  echo "--- ${script}.py ---"
  if [[ "$DRY" -eq 1 ]]; then
    "$PYTHON" "scripts/${script}.py" --dry-run "${TENANT_ARGS[@]}"
  else
    "$PYTHON" "scripts/${script}.py" "${TENANT_ARGS[@]}"
  fi
done

echo "Migraciones M1–M9 completadas."
