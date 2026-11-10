# Robo NFC-e

Automacao visual para consultar NFC-e nos portais das SEFAZ por UF, extrair itens/combustiveis do texto capturado e gerar o CSV base a partir de arquivos SPED EFD.

## Estrutura

```text
robo_nfce/
├── cli.py                    # linha de comando unica (python -m robo_nfce ...)
├── config.py                 # UFs: codigo IBGE -> URL e rotina
├── bot/                      # automacao visual (pyautogui)
│   ├── visual.py             # BotVisual: fachada que junta os mixins abaixo
│   ├── mouse.py              # cliques, movimento "humano", areas aleatorias
│   ├── teclado.py            # digitar/colar/copiar
│   ├── navegador.py          # barra de endereco (abrir, recarregar, ler URL)
│   ├── tela.py               # screenshot, OCR, esperar tela estabilizar
│   ├── audio.py              # reconhecimento de voz
│   └── area_transferencia.py # clipboard com fallback tkinter
├── rotinas/                  # roteiro de cada UF
│   ├── base.py               # RotinaEstado (fluxo comum)
│   ├── registro.py           # nome da rotina -> classe (criar_rotina)
│   ├── mg/rotina.py          # MG: automacao
│   ├── mg/classificacao.py   # MG: classificacao do texto da pagina (testavel)
│   ├── es.py, rj.py          # ES / RJ
│   └── audio.py              # SP / BA (captcha de audio)
├── processamento/lote.py     # le CSV, consulta cada chave, grava CSV enriquecido
├── extracao/                 # texto da NFC-e -> campos/itens
│   ├── nfce.py               # extrair_campos_nfce
│   ├── combustivel.py        # regras de combustivel
│   ├── formatacao.py         # numeros no formato BR
│   ├── linhas.py             # aplicar campos / expandir 1 linha por item
│   └── textos_capturados.py  # gerar/atualizar CSV a partir de .txt
├── sped/                     # SPED EFD -> CSV base
│   ├── parser.py             # registros C100/C170
│   ├── modelos.py            # NotaC100, ItemC170
│   └── arquivos.py           # .txt/.zip/pasta, selecao por periodo
├── csv_chaves.py             # dividir CSV, comparar chaves, analisar faltantes
├── utils/                    # csv, arquivos/zip, texto
└── ferramentas/              # posicao do mouse, teste de microfone
tests/                        # testes (unittest)
scripts/                      # instalacao e Docker
experimentos/                 # prototipos (ex.: rotina MG com Playwright)
dados/                        # entradas/saidas locais (ignorado pelo git)
```

## Instalacao

### Linux (Ubuntu/Debian)

```bash
./scripts/install_linux.sh
source .venv/bin/activate
```

Instala pacotes de sistema ([requirements-sistema.txt](requirements-sistema.txt)), cria `.venv`, instala [requirements.txt](requirements.txt) e o Firefox do Playwright.

### Windows

```bat
scripts\install_windows.bat
.venv\Scripts\activate.bat
```

Instale tambem o Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki) com o idioma Portuguese.

### Audio (opcional)

```bash
pip install -r requirements-audio.txt
```

### Como pacote (opcional)

```bash
pip install -e .          # disponibiliza o comando `robo-nfce`
pip install -e ".[audio]"
```

## Uso

Todos os comandos: `python -m robo_nfce <comando> --help`. Use `-v` para logs detalhados (ex.: `python -m robo_nfce -v processar ...`).

### 1. SPED -> CSV base

Filtra `C100` modelo `65` (cod_sit `00`/`01`), usa `C170` para itens/combustivel e remove chaves duplicadas.

```bash
python -m robo_nfce sped arquivo-sped.txt --saida dados/entrada.csv
python -m robo_nfce sped "arquivos sped.zip" --saida dados/entrada.csv --pasta-txt-filtrados txt_filtrados
```

Com `.zip`, para cada (periodo, CNPJ) usa apenas a entrega mais antiga.

Colunas: `chave, numero, serie, cod_sit, data, valor_total, tem_itens, tem_combustivel, combustiveis, litros_total, valor_itens_combustivel`.

### 2. Consultar as chaves (robo)

A UF e definida pelos 2 primeiros digitos da chave; o CSV deve conter uma unica UF.

```bash
# simulacao (nao mexe no navegador)
python -m robo_nfce processar dados/entrada.csv --saida dados/resultado.csv --modo simular

# execucao real: deixe o navegador aberto e focado; o robo espera 5s antes de comecar
python -m robo_nfce processar dados/entrada.csv --saida dados/resultado.csv --modo executar

# refaz a chave atual se vier sem itens (ate 2 tentativas extras)
python -m robo_nfce processar dados/entrada.csv --saida dados/resultado.csv --modo executar \
    --repetir-sem-itens --max-tentativas-sem-itens 2

# reprocessa apenas as chaves com tem_itens=nao de um resultado anterior
python -m robo_nfce processar dados/resultado.csv --saida dados/resultado_reprocessado.csv \
    --modo executar --somente-sem-itens
```

Os textos de cada consulta ficam em `textos_capturados/<chave>.txt`, na mesma pasta do CSV de saida.
O CSV de saida mantem as colunas originais e adiciona `uf, arquivo_texto_capturado, nota_numero, nota_emissao, item_descricao, item_qtde, item_un, item_vl_unit, item_vl_total` (uma linha por item).

Mova o mouse para o canto superior esquerdo para interromper o robo (failsafe do pyautogui).

### 3. Textos capturados -> CSV

```bash
# gera CSV novo
python -m robo_nfce extrair dados/textos_capturados --saida dados/resultado.csv
python -m robo_nfce extrair "textos capturados.zip" --saida dados/resultado.csv

# atualiza um CSV existente (somente chaves que tiverem .txt)
python -m robo_nfce extrair dados/textos_capturados --csv-base dados/resultado.csv \
    --saida dados/resultado_atualizado.csv [--somente-sem-itens]
```

### 4. Ferramentas de CSV

```bash
# filtra tem_itens=nao e tem_combustivel=nao e divide ao meio
python -m robo_nfce csv dividir dados/resultado.csv --saida-1 dados/lote_a.csv --saida-2 dados/lote_b.csv

# compara chaves entre dois arquivos (presente_nos_dois / faltando_no_arquivo_1 / faltando_no_arquivo_2)
python -m robo_nfce csv comparar dados/a.csv dados/b.csv --saida dados/comparacao_chaves.csv [--coluna-chave numero]

# linhas da base cuja chave nao esta no conferido (mesmo cabecalho da base)
python -m robo_nfce csv analisar-faltantes dados/base.csv dados/conferido.csv --saida dados/analise_faltantes.csv
```

### 5. Calibracao

```bash
python -m robo_nfce.ferramentas.posicao_mouse        # imprime x,y do mouse a cada segundo
python -m robo_nfce.ferramentas.escutar_microfone    # testa reconhecimento de voz
```

## Adicionar ou ajustar uma UF

1. Cadastre a UF em [robo_nfce/config.py](robo_nfce/config.py) (`codigo_ibge`, `url`, `rotina`).
2. Crie a classe em `robo_nfce/rotinas/` herdando de `RotinaEstado` e implemente `_executar_passos(chave, linha)` usando `self.bot` (cliques, `colar_texto`, `selecionar_tudo_e_copiar`, OCR...). Retorne `self._resultado(texto_capturado=..., observacao=...)`.
3. Registre o nome da rotina em [robo_nfce/rotinas/registro.py](robo_nfce/rotinas/registro.py).

Coordenadas de tela ficam como constantes no topo de cada rotina (ex.: `AREA_CAMPO_CHAVE`).

## Docker (Linux com X11)

Prefira o modo local com `venv`: pyautogui, OCR e clipboard funcionam melhor fora do container. Para Docker:

```bash
./scripts/docker-run.sh dados/entrada.csv dados/resultado.csv executar
```

Monta `/tmp/.X11-unix` e a pasta `dados/`. Nao funciona em Wayland puro, WSL ou Windows.

## Testes

```bash
python -m unittest discover -s tests -t .
```
