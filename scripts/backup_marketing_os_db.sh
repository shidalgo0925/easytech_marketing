#!/usr/bin/env bash
# Backup marketing_os.db (Bloque 1 — cimentación prod)
set -euo pipefail

ROOT="${ACCIO_ROOT:-/opt/easytech_marketing}"
DB="${ACCIO_PLATFORM_DB:-$ROOT/Marketing/platform/marketing_os.db}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/emaccion}"
STAMP="$(date +%Y%m%d-%H%M%S)"

if [[ ! -f "$DB" ]]; then
  echo "No existe la BD: $DB"
  exit 1
fi

mkdir -p "$BACKUP_DIR"
DEST="$BACKUP_DIR/marketing_os-${STAMP}.db"

# Checkpoint WAL si existe
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DB" 'PRAGMA wal_checkpoint(TRUNCATE);' 2>/dev/null || true
fi

cp -a "$DB" "$DEST"
chmod 600 "$DEST"

# Symlink latest
ln -sfn "$DEST" "$BACKUP_DIR/marketing_os-latest.db"

echo "Backup BD: $DEST"

# Retener últimos 14
ls -1t "$BACKUP_DIR"/marketing_os-*.db 2>/dev/null | grep -v latest | tail -n +15 | xargs -r rm -f
