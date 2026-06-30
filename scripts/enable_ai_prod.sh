#!/usr/bin/env bash
# Activa IA en prod: escribe ACCIO_AI_* en .env y valida CODITO.
# Uso: CODITO_HOST=10.x.x.x [CODITO_PORT=4000] ./scripts/enable_ai_prod.sh
set -euo pipefail

ROOT="${ACCIO_ROOT:-/opt/easytech_marketing}"
cd "$ROOT"

HOST="${CODITO_HOST:-}"
PORT="${CODITO_PORT:-4000}"
MODEL="${ACCIO_AI_MODEL:-qwen2.5-coder:7b}"

if [[ -z "$HOST" ]]; then
  echo "ERROR: define CODITO_HOST (IP o hostname del servidor LiteLLM/Ollama)."
  echo "Ejemplo: CODITO_HOST=192.168.1.50 ./scripts/enable_ai_prod.sh"
  exit 1
fi

BASE_URL="http://${HOST}:${PORT}"
ENV_FILE="$ROOT/.env"

upsert() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$ENV_FILE"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

upsert ACCIO_AI_PROVIDER litellm
upsert ACCIO_AI_BASE_URL "$BASE_URL"
upsert ACCIO_AI_MODEL "$MODEL"
upsert ACCIO_AI_ENABLED true
upsert AI_ASSISTANT_ENABLED true

echo "Configurado ACCIO_AI_BASE_URL=$BASE_URL"
echo "Probando conectividad..."
"$ROOT/venv/bin/python3" "$ROOT/scripts/validate_codito_ai.py" || {
  echo "FAIL: no se alcanza LiteLLM en $BASE_URL"
  echo "Si CODITO está en red privada, usa túnel SSH: scripts/codito_ssh_tunnel.sh"
  exit 2
}

echo "Reiniciando servicio..."
sudo systemctl restart easytech-accio-engine
sleep 2
systemctl is-active easytech-accio-engine
echo "OK — IA habilitada en prod."
