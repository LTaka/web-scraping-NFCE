#!/usr/bin/env bash
set -euo pipefail

INPUT_CSV="${1:-exemplo_entrada.csv}"
OUTPUT_CSV="${2:-resultado.csv}"
MODO="${3:-executar}"
IMAGE_NAME="${IMAGE_NAME:-webscraping-nfce}"
DISPLAY_VALUE="${DISPLAY:-:0}"
XSOCK="/tmp/.X11-unix"

if [[ ! -d "$XSOCK" ]]; then
  echo "Pasta $XSOCK nao encontrada." >&2
  echo "O Docker com interface grafica so funciona em Linux com X11." >&2
  echo "Use o modo local com venv se estiver em Wayland puro, WSL ou Windows." >&2
  exit 1
fi

echo "Liberando acesso local do Docker ao X11..."
xhost +local:docker >/dev/null 2>&1 || true

echo "Montando imagem Docker..."
docker build -t "$IMAGE_NAME" .

echo "Executando container com acesso ao display do host..."
docker run --rm -it \
  -e DISPLAY="$DISPLAY_VALUE" \
  -v "$XSOCK:$XSOCK" \
  -v "$(pwd):/app" \
  -w /app \
  "$IMAGE_NAME" \
  python3 processar_csv.py "$INPUT_CSV" --saida "$OUTPUT_CSV" --modo "$MODO"
