#!/usr/bin/env bash
# Procesa la siguiente orden Accio pendiente (cron cada 15 min).
set -euo pipefail
cd /opt/easytech_marketing
set -a
source .env
set +a
TENANT="${ACCIO_DEFAULT_TENANT:-easytech}"
curl -sf -X POST \
  -H "Authorization: Bearer ${ACCIO_API_KEY}" \
  "http://127.0.0.1:${ACCIO_ENGINE_PORT:-8092}/accio/${TENANT}/tick" \
  | python3 -m json.tool
