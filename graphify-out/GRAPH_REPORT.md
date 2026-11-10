# Graph Report - .  (2026-07-21)

## Corpus Check
- Corpus is ~11,232 words - fits in a single context window. You may not need a graph.

## Summary
- 248 nodes · 575 edges · 13 communities (7 shown, 6 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

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
- [[_COMMUNITY_Virtual environment setup|Virtual environment setup]]

## God Nodes (most connected - your core abstractions)
1. `BotVisual` - 70 edges
2. `RotinaMGPadrao` - 31 edges
3. `ConfigUF` - 21 edges
4. `extrair_campos_nfce()` - 17 edges
5. `RotinaEstado` - 15 edges
6. `processar_csv()` - 13 edges
7. `RotinaEstado` - 13 edges
8. `criar_rotina()` - 11 edges
9. `RotinaESPadrao` - 9 edges
10. `RotinaESPadrao` - 9 edges

## Surprising Connections (you probably didn't know these)
- `ResultadoProcessamento` --uses--> `BotVisual`  [INFERRED]
  processar_csv.py → bot_visual.py
- `RotinaBAComAudio` --uses--> `BotVisual`  [INFERRED]
  rotinas_estaduais.py → bot_visual.py
- `RotinaESPadrao` --uses--> `BotVisual`  [INFERRED]
  rotinas_estaduais.py → bot_visual.py
- `RotinaEstado` --uses--> `BotVisual`  [INFERRED]
  rotinas_estaduais.py → bot_visual.py
- `RotinaMGPadrao` --uses--> `BotVisual`  [INFERRED]
  rotinas_estaduais.py → bot_visual.py

## Import Cycles
- None detected.

## Communities (13 total, 6 thin omitted)

### Community 0 - "State configuration"
Cohesion: 0.10
Nodes (21): ABC, ConfigUF, extrair_codigo_estado(), obter_config_por_chave(), criar_rotina(), RotinaBAComAudio, RotinaESPadrao, RotinaEstado (+13 more)

### Community 1 - "Visual automation"
Cohesion: 0.10
Nodes (3): BotVisual, roteiro_exemplo(), roteiro_exemplo()

### Community 2 - "NFC-e extraction"
Cohesion: 0.11
Nodes (33): _aplicar_campos_nfce_na_linha(), atualizar_csv_existente_com_textos(), br_decimal(), carregar_textos_por_chave(), criar_parser(), decimal_br(), _deduplicar_itens(), dinheiro_br() (+25 more)

### Community 4 - "SPED import"
Cohesion: 0.18
Nodes (24): analisar_nome_arquivo_sped(), carregar_notas_de_entrada(), criar_parser(), deduplicar_notas_por_chave(), eh_combustivel(), escrever_csv(), extrair_txts_selecionados_de_zip(), formatar_data_sped() (+16 more)

### Community 5 - "CSV batch processing"
Cohesion: 0.19
Nodes (22): DictReader, _aguardar_preparacao_inicial(), _aplicar_campos_nfce_na_linha(), _calcular_total_tentativas(), _carregar_linhas_entrada(), _criar_contexto_lote(), criar_parser(), _deve_repetir_por_sem_itens() (+14 more)

### Community 6 - "CSV key utilities"
Cohesion: 0.40
Nodes (12): coletar_chaves(), comparar_chaves_csv(), criar_parser(), dividir_csv_filtrado(), dividir_lista_ao_meio(), escrever_csv(), filtrar_linhas_sem_itens_e_sem_combustivel(), gerar_analise_faltantes_da_base() (+4 more)

## Knowledge Gaps
- **4 isolated node(s):** `docker-run.sh script`, `install_linux.sh script`, `setup_venv.sh script`, `BotVisualStub`
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BotVisual` connect `Visual automation` to `State configuration`, `Minas Gerais routine`, `CSV batch processing`?**
  _High betweenness centrality (0.366) - this node is a cross-community bridge._
- **Why does `RotinaMGPadrao` connect `Minas Gerais routine` to `State configuration`, `Visual automation`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `processar_csv()` connect `CSV batch processing` to `Retry workflow tests`, `Visual automation`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `BotVisual` (e.g. with `ResultadoProcessamento` and `RotinaBAComAudio`) actually correct?**
  _`BotVisual` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `RotinaMGPadrao` (e.g. with `criar_rotina()` and `BotVisual`) actually correct?**
  _`RotinaMGPadrao` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `ConfigUF` (e.g. with `RotinaBAComAudio` and `RotinaESPadrao`) actually correct?**
  _`ConfigUF` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `RotinaEstado` (e.g. with `BotVisual` and `ConfigUF`) actually correct?**
  _`RotinaEstado` has 2 INFERRED edges - model-reasoned connections that need verification._