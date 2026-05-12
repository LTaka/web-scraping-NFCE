# SPED TRANSFORMA EM CSV

```bash
source .venv/bin/activate
python ler_sped_c100.py "24093799000176-0026978650021-20210501-20210531-0-6C559E76740D29FD9C7C180291390FC122F472C5-SPED-EFD.txt" --saida exemplo_entrada.csv
```
ou 
` ``bash
python3 ler_sped_c100.py "24093799000176-0026978650021-20210501-20210531-0-6C559E76740D29FD9C7C180291390FC122F472C5-SPED-EFD.txt" --saida exemplo_entrada.csv
```

# Robo por UF

Projeto para:

- instalar rapido em maquina nova
- rodar local com `venv`
- usar Docker no Linux com X11 quando fizer sentido
- ler um CSV e executar a rotina por UF
- completar o CSV com os dados capturados

## 1. Recomendacao pratica

Use o modo local com `venv` como caminho principal.

Motivo:

- `pyautogui` controla mouse e teclado da maquina real
- OCR e clipboard funciona m melhor fora do container
- evita erros de `Xlib.xauth`, `XAUTHORITY` e permissao de display

Deixe o Docker como alternativa secundaria para Linux com X11.

## 2. Instalacao rapida no Linux

Em Ubuntu/Debian:

```bash
chmod +x install_linux.sh
./install_linux.sh
source .venv/bin/activate
```

Esse script:

- instala dependencias do sistema
- cria `.venv`
- instala dependencias Python
- instala o Firefox do Playwright

Se quiser audio de microfone:

```bash
source .venv/bin/activate
pip install -r requirements-audio.txt
```

## 3. Instalacao rapida no Windows

No Prompt de Comando:

```bat
install_windows.bat
```

Depois ative:

```bat
.venv\Scripts\activate.bat
```

No Windows o script instala a parte Python. Para OCR, ainda precisa instalar o Tesseract manualmente:

- `https://github.com/UB-Mannheim/tesseract/wiki`
- durante a instalacao, inclua o idioma `Portuguese`

O instalador tambem baixa o navegador `Firefox` do Playwright.

Se quiser audio de microfone:

```bat
pip install -r requirements-audio.txt
```

## 4. Docker no Linux

Use Docker apenas se:

- voce estiver em Linux
- sua sessao grafica tiver X11 disponivel
- quiser isolar o ambiente

Rodar:

```bash
chmod +x docker-run.sh
./docker-run.sh exemplo_entrada.csv resultado.csv executar
```

O script:

- libera acesso local do Docker ao X11 com `xhost +local:docker`
- monta `/tmp/.X11-unix`
- executa o bot dentro do container

Limites importantes:

- em Wayland puro, WSL e Windows o Docker grafico tende a dar problema
- se aparecer erro de display, prefira o modo local com `venv`
- este projeto nao depende de Docker para funcionar

## 5. Onde configurar os links por estado

Edite [config_ufs.py](/home/linx/Documentos/www/web-scraping-NFCE/config_ufs.py).

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

## 6. Onde criar a rotina de cada estado

Edite [rotinas_estaduais.py](/home/linx/Documentos/www/web-scraping-NFCE/rotinas_estaduais.py).

Classes de exemplo:

- `RotinaMGPadrao`
- `RotinaESComAudio`

Em cada uma voce vai colocar:

- cliques (`self.bot.clicar(x, y)`)
- digitacao (`self.bot.escrever(...)`)
- tabs e enter (`self.bot.pressionar(...)`)
- leitura OCR da tela
- captura de audio, quando precisar

## 7. Como processar o CSV

Exemplo em modo simulacao:

```bash
source .venv/bin/activate
python processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo simular
```

Para rodar de verdade:

```bash
source .venv/bin/activate
python processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo executar
```

## 8. Como gerar o CSV a partir do SPED

Para ler um arquivo `SPED EFD`, filtrar os registros `C100` de modelo `65` e gerar o CSV base do robo:

```bash
python ler_sped_c100.py arquivo-sped.txt --saida exemplo_entrada.csv
```

O CSV gerado sai com estas colunas:

- `chave`
- `numero`
- `serie`
- `cod_sit`
- `data`
- `valor_total`
- `tem_itens`
- `tem_combustivel`
- `combustiveis`
- `litros_total`
- `valor_itens_combustivel`

Quando o SPED tiver registros `C170`, o script usa esses itens para preencher `tem_itens` e os campos de combustivel. Se o arquivo tiver apenas `C100` e `C190`, esses campos ficam vazios ou com `nao`.

## 9. Colunas adicionadas no CSV de saida

O script preserva as colunas originais e adiciona:

- `uf`
- `url_consulta`
- `status_robo`
- `arquivo_texto_capturado`
- `observacao`
- `nota_numero`
- `nota_emissao`
- `item_descricao`
- `item_qtde`
- `item_un`
- `item_vl_unit`
- `item_vl_total`

## 10. Dependencias do projeto

Python:

- [requirements.txt](/home/linx/Documentos/www/web-scraping-NFCE/requirements.txt)
- [requirements-audio.txt](/home/linx/Documentos/www/web-scraping-NFCE/requirements-audio.txt)

Se for instalar manualmente o Playwright:

```bash
python3 -m pip install playwright
python3 -m playwright install firefox
```

Sistema Linux/Ubuntu:

- [requirements-sistema.txt](/home/linx/Documentos/www/web-scraping-NFCE/requirements-sistema.txt)

## 11. Arquivos principais

- [bot_visual.py](/home/linx/Documentos/www/web-scraping-NFCE/bot_visual.py): funcoes base de automacao, OCR e audio
- [config_ufs.py](/home/linx/Documentos/www/web-scraping-NFCE/config_ufs.py): links e configuracao por estado
- [rotinas_estaduais.py](/home/linx/Documentos/www/web-scraping-NFCE/rotinas_estaduais.py): roteiro de cada UF
- [processar_csv.py](/home/linx/Documentos/www/web-scraping-NFCE/processar_csv.py): le o CSV e chama a rotina certa
- [mouse_posicao.py](/home/linx/Documentos/www/web-scraping-NFCE/mouse_posicao.py): mostra a posicao do mouse para descobrir coordenadas
- [install_linux.sh](/home/linx/Documentos/www/web-scraping-NFCE/install_linux.sh): instalacao completa no Linux
- [install_windows.bat](/home/linx/Documentos/www/web-scraping-NFCE/install_windows.bat): instalacao base no Windows
- [docker-run.sh](/home/linx/Documentos/www/web-scraping-NFCE/docker-run.sh): execucao Docker simplificada no Linux
