#!/usr/bin/env bash
# Copia el último PNG subido en Cursor assets → Marketing/flyers/
# Uso: ./scripts/import_flyer.sh 10_iius.png

set -euo pipefail
ASSETS="/home/papichulo/.cursor/projects/opt/assets"
DEST="/opt/easytech_marketing/Marketing/flyers"

if [[ $# -lt 1 ]]; then
  echo "Uso: $0 <nombre_destino.png>"
  echo "Ejemplo: $0 10_iius.png"
  exit 1
fi

TARGET="$DEST/$1"
LATEST=$(ls -t "$ASSETS"/*.png 2>/dev/null | head -1)

if [[ -z "${LATEST:-}" ]]; then
  echo "No hay PNG en $ASSETS"
  exit 1
fi

cp "$LATEST" "$TARGET"
echo "Copiado: $LATEST → $TARGET"
echo "Recuerda actualizar Marketing/flyers/manifest.json"
