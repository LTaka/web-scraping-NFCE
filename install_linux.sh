#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 nao encontrado. Instale Python 3.10+ antes de continuar." >&2
  exit 1
fi

echo "Instalando dependencias de sistema (Ubuntu/Debian)..."
sudo apt-get update
sudo apt-get install -y $(grep -v '^#' requirements-sistema.txt | grep -v '^[[:space:]]*$')

echo "Criando ambiente virtual..."
python3 -m venv .venv
source .venv/bin/activate

echo "Atualizando pip e instalando dependencias Python..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo
echo "Instalacao concluida."
echo "Ative com: source .venv/bin/activate"
echo "Se for usar microfone, rode: pip install -r requirements-audio.txt"
