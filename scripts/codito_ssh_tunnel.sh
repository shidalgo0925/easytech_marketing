#!/usr/bin/env bash
# Túnel SSH local → LiteLLM en CODITO (puerto 4000 en remoto).
# Uso: CODITO_SSH=user@CODITO_HOST ./scripts/codito_ssh_tunnel.sh
# Luego en .env: ACCIO_AI_BASE_URL=http://127.0.0.1:14000
set -euo pipefail

REMOTE="${CODITO_SSH:-}"
LOCAL_PORT="${CODITO_LOCAL_PORT:-14000}"
REMOTE_PORT="${CODITO_REMOTE_PORT:-4000}"

if [[ -z "$REMOTE" ]]; then
  echo "Uso: CODITO_SSH=usuario@host-codito $0"
  exit 1
fi

echo "Túnel: localhost:${LOCAL_PORT} -> ${REMOTE}:${REMOTE_PORT}"
echo "En .env: ACCIO_AI_BASE_URL=http://127.0.0.1:${LOCAL_PORT}"
exec ssh -N -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" "$REMOTE"
