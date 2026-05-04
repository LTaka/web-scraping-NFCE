#!/usr/bin/env bash
set -euo pipefail

INPUT_CSV="${1:-exemplo_entrada.csv}"
OUTPUT_CSV="${2:-resultado.csv}"
MODO="${3:-executar}"
XAUTH_FILE="${XAUTHORITY:-$HOME/.Xauthority}"

if [[ ! -f "$XAUTH_FILE" ]]; then
  echo "Arquivo Xauthority nao encontrado: $XAUTH_FILE" >&2
  echo "Defina XAUTHORITY no host ou inicie uma sessao grafica com X11 antes de rodar o container." >&2
  exit 1
fi

docker build -t webscarping-bot .

docker run --rm -it \
  -e DISPLAY="${DISPLAY:-:0}" \
  -e XAUTHORITY=/tmp/.docker.xauth \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$XAUTH_FILE:/tmp/.docker.xauth:ro" \
  -v "$(pwd)":/app \
  -w /app \
  webscarping-bot \
  python3 processar_csv.py "$INPUT_CSV" --saida "$OUTPUT_CSV" --modo "$MODO"
