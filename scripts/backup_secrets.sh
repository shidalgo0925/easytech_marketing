#!/usr/bin/env bash
# Backup cifrado de secretos EM+Acción (Fase A V2)
# Uso: BACKUP_GPG_PASSPHRASE='tu-frase' ./scripts/backup_secrets.sh
set -euo pipefail

ROOT="${ACCIO_ROOT:-/opt/easytech_marketing}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/emaccion}"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="$BACKUP_DIR/emaccion-secrets-$STAMP.tar.gz"
ENCRYPTED="$ARCHIVE.gpg"

mkdir -p "$BACKUP_DIR"

FILES=()
[[ -f "$ROOT/.env" ]] && FILES+=(".env")
[[ -f "$ROOT/deploy/secrets/.env.prod" ]] && FILES+=("deploy/secrets/.env.prod")
[[ -f "$ROOT/deploy/secrets/.env.dev" ]] && FILES+=("deploy/secrets/.env.dev")
[[ -f "$ROOT/deploy/secrets/.env.test" ]] && FILES+=("deploy/secrets/.env.test")
[[ -d "$ROOT/Marketing/tenants/.secrets" ]] && FILES+=("Marketing/tenants/.secrets")

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "No hay archivos de secretos para respaldar en $ROOT"
  exit 1
fi

tar -czf "$ARCHIVE" -C "$ROOT" "${FILES[@]}"
chmod 600 "$ARCHIVE"

if command -v gpg >/dev/null 2>&1; then
  if [[ -z "${BACKUP_GPG_PASSPHRASE:-}" ]]; then
    echo "Sin BACKUP_GPG_PASSPHRASE — solo tar.gz en $ARCHIVE"
    exit 0
  fi
  echo "$BACKUP_GPG_PASSPHRASE" | gpg --batch --yes --passphrase-fd 0 \
    --symmetric --cipher-algo AES256 -o "$ENCRYPTED" "$ARCHIVE"
  rm -f "$ARCHIVE"
  chmod 600 "$ENCRYPTED"
  echo "Backup cifrado: $ENCRYPTED"
else
  echo "gpg no instalado — backup sin cifrar: $ARCHIVE"
fi

# Retener últimos 14 backups
ls -1t "$BACKUP_DIR"/emaccion-secrets-* 2>/dev/null | tail -n +15 | xargs -r rm -f
