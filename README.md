# Robo por UF

Estrutura inicial para:

- rodar em `venv`
- instalar dependencias
- ler um CSV
- identificar a UF pelos 2 primeiros digitos da chave da primeira coluna
- abrir o link correto da UF
- executar uma rotina especifica por estado
- completar o CSV com os dados capturados

## 1. Criar e ativar o ambiente

```bash
chmod +x setup_venv.sh
./setup_venv.sh
source .venv/bin/activate
```

Esse passo instala o ambiente base sem depender de microfone.

## Docker

Para rodar em Docker com acesso ao display do host:

```bash
chmod +x docker-run.sh
xhost +local:docker
./docker-run.sh exemplo_entrada.csv resultado.csv executar
```

Comandos equivalentes:

```bash
docker build -t webscarping-bot .
docker run --rm -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)":/app \
  -w /app \
  webscarping-bot \
  python3 processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo executar
```

Observacao:

- como o projeto usa `pyautogui`, o container precisa acessar a sessao grafica do host
- se o `Ctrl+C` ou `Ctrl+V` nao funcionar no container, rode antes `xhost +local:docker`

## 2. Habilitar audio do microfone

Se voce precisar usar `ouvir_microfone()`, instale antes as bibliotecas do sistema:

```bash
sudo apt-get install portaudio19-dev python3-dev tesseract-ocr tesseract-ocr-por
```

Depois instale o pacote opcional:

```bash
source .venv/bin/activate
pip install -r requirements-audio.txt
```

## 3. Onde configurar os links por estado

Edite [config_ufs.py](/home/linx/Documentos/www/webscarping/config_ufs.py).

Hoje o arquivo ja vem com estes exemplos:

- `31 -> MG -> https://preencher-link-mg-aqui`
- `32 -> ES -> https://preencher-link-es-aqui`

Cada UF tem:

- codigo IBGE de 2 digitos
- sigla
- nome
- link de entrada
- nome da rotina
- se usa audio ou nao

## 4. Onde criar a rotina de cada estado

Edite [rotinas_estaduais.py](/home/linx/Documentos/www/webscarping/rotinas_estaduais.py).

Ja deixei duas classes prontas:

- `RotinaMGPadrao`
- `RotinaESComAudio`

Em cada uma voce vai colocar:

- cliques (`self.bot.clicar(x, y)`)
- digitacao (`self.bot.escrever(...)`)
- tabs e enter (`self.bot.pressionar(...)`)
- leitura OCR da tela
- captura de audio, quando precisar

## 5. Como processar o CSV

Exemplo:

```bash
source .venv/bin/activate
python processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo simular
```

Para rodar de verdade:

```bash
python processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo executar
```

## 6. Colunas adicionadas no CSV de saida

O script preserva as colunas originais e adiciona:

- `uf`
- `url_consulta`
- `status_robo`
- `texto_capturado`
- `texto_audio`
- `observacao`

## 7. Arquivos principais

- [bot_visual.py](/home/linx/Documentos/www/webscarping/bot_visual.py): funcoes base de automacao, OCR e audio
- [config_ufs.py](/home/linx/Documentos/www/webscarping/config_ufs.py): links e configuracao por estado
- [rotinas_estaduais.py](/home/linx/Documentos/www/webscarping/rotinas_estaduais.py): roteiro de cada UF
- [processar_csv.py](/home/linx/Documentos/www/webscarping/processar_csv.py): le o CSV e chama a rotina certa
- [mouse_posicao.py](/home/linx/Documentos/www/webscarping/mouse_posicao.py): mostra a posicao do mouse para descobrir coordenadas
- [requirements-audio.txt](/home/linx/Documentos/www/webscarping/requirements-audio.txt): dependencias opcionais para captura do microfone
