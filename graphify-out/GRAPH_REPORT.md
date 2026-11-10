# Graph Report - web-scraping-NFCE  (2026-11-10)

## Corpus Check
- 53 files · ~11,182 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 388 nodes · 783 edges · 25 communities (17 shown, 8 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `73642aad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_State configuration|State configuration]]
- [[_COMMUNITY_Visual automation|Visual automation]]
- [[_COMMUNITY_NFC-e extraction|NFC-e extraction]]
- [[_COMMUNITY_Minas Gerais routine|Minas Gerais routine]]
- [[_COMMUNITY_SPED import|SPED import]]
- [[_COMMUNITY_CSV batch processing|CSV batch processing]]
- [[_COMMUNITY_CSV key utilities|CSV key utilities]]
- [[_COMMUNITY_CSV utility tests|CSV utility tests]]
- [[_COMMUNITY_Retry workflow tests|Retry workflow tests]]
- [[_COMMUNITY_Docker runner|Docker runner]]
- [[_COMMUNITY_Linux installation|Linux installation]]
- [[_COMMUNITY_Mouse helper|Mouse helper]]
- [[_COMMUNITY_Virtual environment setup|Virtual environment setup]]
- [[_COMMUNITY_UtilCsvChavesTests|UtilCsvChavesTests]]
- [[_COMMUNITY_posicao_mouse.py|posicao_mouse.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_docker-run.sh|docker-run.sh]]
- [[_COMMUNITY_install_linux.sh|install_linux.sh]]
- [[_COMMUNITY_setup_venv.sh|setup_venv.sh]]

## God Nodes (most connected - your core abstractions)
1. `BotVisual` - 29 edges
2. `RotinaEstado` - 24 edges
3. `extrair_campos_nfce()` - 22 edges
4. `ConfigUF` - 21 edges
5. `RotinaMGPadrao` - 19 edges
6. `TecladoMixin` - 16 edges
7. `RotinaEstado` - 15 edges
8. `MouseMixin` - 14 edges
9. `TelaMixin` - 14 edges
10. `processar_csv()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `RotinaEstado` --uses--> `BotVisual`  [INFERRED]
  experimentos/rotinas_playwright.py → robo_nfce/bot/visual.py
- `RotinaEstado` --uses--> `ConfigUF`  [INFERRED]
  experimentos/rotinas_playwright.py → robo_nfce/config.py
- `RotinaMGPlaywright` --uses--> `BotVisual`  [INFERRED]
  experimentos/rotinas_playwright.py → robo_nfce/bot/visual.py
- `RotinaMGPlaywright` --uses--> `ConfigUF`  [INFERRED]
  experimentos/rotinas_playwright.py → robo_nfce/config.py
- `RotinaMGPadrao` --uses--> `BotVisual`  [INFERRED]
  experimentos/rotinas_playwright.py → robo_nfce/bot/visual.py

## Import Cycles
- None detected.

## Communities (25 total, 8 thin omitted)

### Community 0 - "State configuration"
Cohesion: 0.11
Nodes (15): ABC, Modelo de rotina com captcha de audio (ainda nao calibrada).      Fluxo esperado, RotinaBAComAudio, RotinaSPComAudio, Fluxo base: prepara a pagina da UF e executa os passos da consulta de uma chave., Abre a URL da UF na primeira chave e recarrega nas seguintes., RotinaEstado, Consulta no portal do ES: sucesso = URL mudar para a pagina do DANFE. (+7 more)

### Community 1 - "Visual automation"
Cohesion: 0.10
Nodes (34): analisar_nome_arquivo_sped(), carregar_notas_de_entrada(), deduplicar_notas_por_chave(), _filtrar_nomes_por_periodo(), gerar_csv_base_do_sped(), Path, Selecao de arquivos SPED (.txt, .zip ou pasta) e conversao para o CSV base., Converte SPED (.txt, .zip ou pasta) no CSV base do robo. Retorna o total de nota (+26 more)

### Community 2 - "NFC-e extraction"
Cohesion: 0.11
Nodes (28): descricao_tem_combustivel(), eh_item_combustivel(), limpar_descricao_combustivel(), Regras para identificar itens de combustivel., Combustivel = descricao com nome de combustivel E unidade de volume.      Evita, br_decimal(), decimal_br(), dinheiro_br() (+20 more)

### Community 3 - "Minas Gerais routine"
Cohesion: 0.13
Nodes (16): consultar_com_retry(), consultar_nfce_mg(), _consultar_nfce_mg_em_pagina(), criar_rotina(), RotinaBAComAudio, RotinaESPadrao, RotinaEstado, RotinaMGPadrao (+8 more)

### Community 4 - "SPED import"
Cohesion: 0.10
Nodes (14): Screenshots, OCR e esperas baseadas no conteudo da tela., Hash de uma miniatura em tons de cinza: muda quando a tela muda., Tenta Ctrl+A/Ctrl+C; se vier pouco texto, cai para OCR rolando a pagina., TelaMixin, classificar_estado_pagina(), eh_pagina_erro(), eh_pagina_inicial(), eh_resultado() (+6 more)

### Community 5 - "CSV batch processing"
Cohesion: 0.12
Nodes (29): DictReader, extrair_codigo_estado(), obter_config_por_chave(), Configuracao das UFs suportadas (codigo IBGE -> URL e rotina)., aplicar_campos_nfce(), _com_item(), expandir_por_itens(), Aplicacao dos campos extraidos da NFC-e nas linhas do CSV. (+21 more)

### Community 6 - "CSV key utilities"
Cohesion: 0.09
Nodes (8): Clipboard com fallback para tkinter quando o pyperclip nao tem backend., AudioMixin, Reconhecimento de voz (Google Speech) a partir de arquivo ou microfone., MouseMixin, Move em curva suave com pequenos desvios aleatorios, simulando um humano., Movimentos e cliques. Espera que a classe final defina `esperar`., NavegadorMixin, Acoes na barra de endereco do navegador ja aberto e focado.

### Community 7 - "CSV utility tests"
Cohesion: 0.14
Nodes (25): coletar_chaves(), comparar_chaves_csv(), dividir_csv_filtrado(), dividir_lista_ao_meio(), filtrar_linhas_sem_itens_e_sem_combustivel(), gerar_analise_faltantes_da_base(), Path, Ferramentas para dividir CSVs e comparar chaves entre arquivos. (+17 more)

### Community 8 - "Retry workflow tests"
Cohesion: 0.24
Nodes (16): ArgumentParser, _caminho_opcional(), _cmd_csv_analisar(), _cmd_csv_comparar(), _cmd_csv_dividir(), _cmd_extrair(), _cmd_processar(), _cmd_sped() (+8 more)

### Community 9 - "Docker runner"
Cohesion: 0.22
Nodes (3): Consulta no portal de MG: valida cada etapa pelo texto copiado da pagina (Ctrl+A, Preenche a chave conforme o layout atual e retorna o ponto do botao consultar., RotinaMGPadrao

### Community 10 - "Linux installation"
Cohesion: 0.12
Nodes (16): 1. SPED -> CSV base, 2. Consultar as chaves (robo), 3. Textos capturados -> CSV, 4. Ferramentas de CSV, 5. Calibracao, Adicionar ou ajustar uma UF, Audio (opcional), Como pacote (opcional) (+8 more)

### Community 11 - "Mouse helper"
Cohesion: 0.20
Nodes (4): Cola via clipboard; se indisponivel, digita caractere a caractere., Como `escrever`, mas falha se nao conseguir usar o clipboard., Teclado, colagem e copia. Espera `esperar`, `clicar`, `arrastar` e `mover_e_clic, TecladoMixin

### Community 12 - "Virtual environment setup"
Cohesion: 0.21
Nodes (4): FiltroEntradaTests, _resposta(), RetentativaTests, RotinaSequencialStub

## Knowledge Gaps
- **16 isolated node(s):** `docker-run.sh script`, `install_linux.sh script`, `setup_venv.sh script`, `Estrutura`, `Linux (Ubuntu/Debian)` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BotVisual` connect `Minas Gerais routine` to `State configuration`, `SPED import`, `CSV batch processing`, `CSV key utilities`, `Mouse helper`?**
  _High betweenness centrality (0.288) - this node is a cross-community bridge._
- **Why does `RotinaEstado` connect `State configuration` to `Docker runner`, `Minas Gerais routine`, `CSV batch processing`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `escrever_csv()` connect `CSV utility tests` to `Visual automation`, `CSV batch processing`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 15 inferred relationships involving `BotVisual` (e.g. with `RotinaBAComAudio` and `RotinaESPadrao`) actually correct?**
  _`BotVisual` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `RotinaEstado` (e.g. with `ContextoLote` and `ResultadoProcessamento`) actually correct?**
  _`RotinaEstado` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ConfigUF` (e.g. with `RotinaBAComAudio` and `RotinaESPadrao`) actually correct?**
  _`ConfigUF` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Robo de consulta de NFC-e por UF e ferramentas de extracao/SPED.`, `Automacao visual (mouse, teclado, clipboard, OCR e audio).  Importe `BotVisual``, `Clipboard com fallback para tkinter quando o pyperclip nao tem backend.` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._