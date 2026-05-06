@echo off
setlocal

where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado.
  echo Instale Python 3.10+ em https://www.python.org/downloads/windows/
  echo Marque a opcao "Add python.exe to PATH" durante a instalacao.
  exit /b 1
)

echo Criando ambiente virtual...
py -3 -m venv .venv
if errorlevel 1 exit /b 1

call .venv\Scripts\activate.bat
if errorlevel 1 exit /b 1

echo Atualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Instalando dependencias Python...
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Instalacao base concluida.
echo.
echo Passos manuais no Windows:
echo 1. Instale o Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Durante a instalacao, inclua o idioma Portuguese.
echo 3. Se for usar microfone, rode:
echo    pip install -r requirements-audio.txt
echo.
echo Para ativar depois:
echo .venv\Scripts\activate.bat
