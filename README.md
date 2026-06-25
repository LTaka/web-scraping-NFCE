# SPED TRANSFORMA EM CSV

```bash
source .venv/bin/activate
python ler_sped_c100.py "24093799000176-0026978650021-20210501-20210531-0-6C559E76740D29FD9C7C180291390FC122F472C5-SPED-EFD.txt" --saida exemplo_entrada.csv
```

Ou:

```bash
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

Se quiser repetir apenas as chaves que terminarem com `tem_itens=nao`:

```bash
source .venv/bin/activate
python processar_csv.py exemplo_entrada.csv --saida resultado.csv --modo executar --repetir-sem-itens --max-tentativas-sem-itens 2
```

Esse modo refaz somente a consulta da chave atual quando o texto capturado nao gerar itens, sem reprocessar o lote inteiro.

Se voce ja tem um `resultado.csv` pronto e quer rodar de novo somente as chaves que ficaram com `tem_itens=nao`:

```bash
source .venv/bin/activate
python processar_csv.py resultado.csv --saida resultado_reprocessado.csv --modo executar --somente-sem-itens
```

Esse comando le o CSV final, filtra apenas as linhas com `tem_itens=nao` e deduplica por chave antes de rodar novamente.

## 8. Como gerar o CSV a partir do SPED

Para ler um arquivo `SPED EFD`, filtrar os registros `C100` de modelo `65` e gerar o CSV base do robo:

```bash
python ler_sped_c100.py arquivo-sped.txt --saida exemplo_entrada.csv
```

Tambem aceita `.zip` com varios SPEDs:

```bash
python3 ler_sped_c100.py arquivo.zip --saida exemplo_entrada.csv
```

```bash
python3 ler_sped_c100.py "arquivos com espacamento.zip" --saida exemplo_entrada.csv --pasta-txt-filtrados txt_filtrados
```

O script extrai os `.txt`, le os SPEDs e remove chaves duplicadas no CSV final, mantendo a primeira ocorrencia de cada chave.

O CSV base gerado sai com estas colunas:

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

## 9. Como transformar `textos_capturados` em `resultado.csv`

Se voce ja tem uma pasta `textos_capturados` com arquivos `.txt`, o `extrator_nfce.py` le esses textos e monta um `resultado.csv`:

```bash
python3 extrator_nfce.py textos_capturados --saida resultado1.csv
```

Tambem aceita um `.zip` com os textos capturados:

```bash
python3 extrator_nfce.py textos_capturados.zip --saida resultado.csv
```

Ou com caminho contendo espacos:

```bash
python3 extrator_nfce.py "textos capturados.zip" --saida resultado.csv --pasta-txt-filtrados txt_filtrados
```

Esse fluxo usa o nome do arquivo `.txt` como chave e extrai:

- `nota_numero`
- `nota_emissao`
- `tem_itens`
- `tem_combustivel`
- `combustiveis`
- `litros_total`
- `valor_itens_combustivel`
- itens detalhados em linhas expandidas

## 10. Como atualizar um CSV ja existente com os textos capturados

Se voce ja tem um CSV pronto, por exemplo gerado pelo `ler_sped_c100.py`, pode enriquecer esse CSV com os textos que existirem em `textos_capturados`.

Atualizando todas as chaves que tiverem `.txt` correspondente:

```bash
python3 extrator_nfce.py textos_capturados --csv-base resultado.csv --saida resultado_atualizado.csv
```

Atualizando apenas as linhas que hoje estao com `tem_itens=nao`:

```bash
python3 extrator_nfce.py textos_capturados --csv-base resultado.csv --saida resultado_atualizado.csv --somente-sem-itens
```

Regras desse modo:

- se a chave do CSV nao tiver `.txt`, a linha fica como esta
- se existir `.txt` para a chave, os campos de NFC-e sao recalculados
- se houver itens no texto, o script expande a saida em multiplas linhas, uma por item
- quando usar `--somente-sem-itens`, linhas com `tem_itens=sim` permanecem intactas

## 11. Como dividir um CSV em `entrada_1.csv` e `entrada_2.csv`

Se voce receber um CSV com colunas como:

```text
chave,numero,serie,cod_sit,data,valor_total,tem_itens,tem_combustivel,combustiveis,litros_total,valor_itens_combustivel,uf,url_consulta,status_robo,arquivo_texto_capturado,observacao,nota_numero,nota_emissao,item_descricao,item_qtde,item_un,item_vl_unit,item_vl_total
```

e quiser separar apenas as linhas em que:

- `tem_itens=nao`
- `tem_combustivel=nao`

use:

```bash
python3 util_csv_chaves.py dividir resultado.csv
```

Isso gera:

- `entrada_1.csv`
- `entrada_2.csv`

O script:

- le o CSV informado
- filtra somente as linhas com os dois campos iguais a `nao`
- divide o resultado em duas metades
- deixa a primeira metade em `entrada_1.csv`
- deixa a segunda metade em `entrada_2.csv`

Se quiser nomes diferentes:

```bash
python3 util_csv_chaves.py dividir mva31.csv --saida-1 lote_a.csv --saida-2 lote_b.csv
```

## 12. Como comparar as chaves entre dois CSVs

Para conferir se todas as chaves de um arquivo existem no outro e identificar faltantes:

```bash
python3 util_csv_chaves.py comparar entrada_1.csv entrada_2.csv --saida comparacao_chaves.csv
```

O arquivo `comparacao_chaves.csv` sai com as colunas:

- `chave`
- `status_comparacao`
- `presente_arquivo_1`
- `presente_arquivo_2`

Possiveis status:

- `presente_nos_dois`
- `faltando_no_arquivo_1`
- `faltando_no_arquivo_2`

Se a coluna da chave tiver outro nome, use por exemplo:

```bash
python3 util_csv_chaves.py comparar arquivo_a.csv arquivo_b.csv --coluna-chave numero
```

## 13. Como gerar uma analise so com o que falta no conferido

Se voce quer um CSV contendo apenas as linhas que estao na base mas nao estao no conferido:

```bash
python3 util_csv_chaves.py analisar-faltantes base.csv conferido.csv --saida analise_faltantes.csv
```

Nesse comando:

- `base.csv` e o arquivo principal
- `conferido.csv` e o arquivo usado para verificar se a chave existe
- `analise_faltantes.csv` recebe somente as linhas da base que nao foram encontradas no conferido

O CSV de saida copia o cabecalho da base exatamente igual, na mesma ordem. Exemplo:

```text
chave,numero,serie,cod_sit,data,valor_total,tem_itens,tem_combustivel,combustiveis,litros_total,valor_itens_combustivel
```

## 14. Colunas adicionadas no CSV de saida

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

## 15. Dependencias do projeto

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

## 16. Arquivos principais

- [bot_visual.py](/home/linx/Documentos/www/web-scraping-NFCE/bot_visual.py): funcoes base de automacao, OCR e audio
- [config_ufs.py](/home/linx/Documentos/www/web-scraping-NFCE/config_ufs.py): links e configuracao por estado
- [rotinas_estaduais.py](/home/linx/Documentos/www/web-scraping-NFCE/rotinas_estaduais.py): roteiro de cada UF
- [processar_csv.py](/home/linx/Documentos/www/web-scraping-NFCE/processar_csv.py): le o CSV base e chama a rotina certa por UF
- [ler_sped_c100.py](/home/linx/Documentos/www/web-scraping-NFCE/ler_sped_c100.py): gera o CSV base a partir de arquivo SPED `.txt`, `.zip` ou pasta
- [extrator_nfce.py](/home/linx/Documentos/www/web-scraping-NFCE/extrator_nfce.py): transforma `textos_capturados` em CSV ou atualiza um CSV existente
- [util_csv_chaves.py](/home/linx/Documentos/www/web-scraping-NFCE/util_csv_chaves.py): divide CSV filtrando `tem_itens=nao` e `tem_combustivel=nao`, e compara chaves entre arquivos
- [mouse_posicao.py](/home/linx/Documentos/www/web-scraping-NFCE/mouse_posicao.py): mostra a posicao do mouse para descobrir coordenadas
- [install_linux.sh](/home/linx/Documentos/www/web-scraping-NFCE/install_linux.sh): instalacao completa no Linux
- [install_windows.bat](/home/linx/Documentos/www/web-scraping-NFCE/install_windows.bat): instalacao base no Windows
- [docker-run.sh](/home/linx/Documentos/www/web-scraping-NFCE/docker-run.sh): execucao Docker simplificada no Linux
