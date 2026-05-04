#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Ambiente criado em .venv"
echo "Ative com: source .venv/bin/activate"
echo "Se quiser habilitar captura de audio do microfone, instale as dependencias do sistema:"
echo "  sudo apt-get install portaudio19-dev python3-dev tesseract-ocr tesseract-ocr-por"
echo "Depois instale o pacote opcional:"
echo "  pip install -r requirements-audio.txt"
