#!/usr/bin/env bash
set -euo pipefail

INPUT_CSV="${1:-exemplo_entrada.csv}"
OUTPUT_CSV="${2:-resultado.csv}"
MODO="${3:-executar}"

docker build -t webscarping-bot .

docker run --rm -it \
  -e DISPLAY="${DISPLAY:-:0}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)":/app \
  -w /app \
  webscarping-bot \
  python3 processar_csv.py "$INPUT_CSV" --saida "$OUTPUT_CSV" --modo "$MODO"
