#!/usr/bin/env bash
# Cliente CLI para Accio → Motor en ArrozConPollo
set -euo pipefail
cd /opt/easytech_marketing
set -a
source .env
set +a
BASE="http://127.0.0.1:${ACCIO_ENGINE_PORT:-8092}"
AUTH=(-H "Authorization: Bearer ${ACCIO_API_KEY}")

cmd="${1:-status}"
shift || true

case "$cmd" in
  status)
    curl -sf "${AUTH[@]}" "$BASE/accio/status" | python3 -m json.tool
    ;;
  orders)
    curl -sf "${AUTH[@]}" "$BASE/accio/orders" | python3 -m json.tool
    ;;
  tick)
    curl -sf -X POST "${AUTH[@]}" "$BASE/accio/tick" | python3 -m json.tool
    ;;
  pipeline)
    curl -sf -X POST "${AUTH[@]}" "$BASE/accio/run/pipeline" | python3 -m json.tool
    ;;
  publish)
    force=""
    [[ "${1:-}" == "--force" ]] && force='{"force":true}'
    curl -sf -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
      -d "${force:-{}}" "$BASE/accio/run/publish-linkedin" | python3 -m json.tool
    ;;
  queue)
    curl -sf "${AUTH[@]}" "$BASE/accio/content/queue" | python3 -m json.tool
    ;;
  *)
    echo "Uso: $0 {status|orders|tick|pipeline|publish [--force]|queue}"
    exit 1
    ;;
esac
