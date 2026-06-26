#!/usr/bin/env bash
# Activa entorno ACCIO_ENV para operación local o deploy
# Uso: source scripts/accio_env.sh prod|dev|test
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_NAME="${1:-prod}"

case "$ENV_NAME" in
  prod|dev|test) ;;
  *)
    echo "Uso: source scripts/accio_env.sh prod|dev|test"
    return 1 2>/dev/null || exit 1
    ;;
esac

export ACCIO_ENV="$ENV_NAME"
export ACCIO_ROOT="$ROOT"

SRC="$ROOT/deploy/secrets/.env.$ENV_NAME"
if [[ ! -f "$SRC" ]]; then
  echo "Falta $SRC — copia desde deploy/environments/.env.$ENV_NAME.example"
  return 1 2>/dev/null || exit 1
fi

echo "ACCIO_ENV=$ACCIO_ENV"
echo "Secrets: $SRC"
