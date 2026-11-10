"""Gera ou atualiza CSVs a partir da pasta de textos capturados (<chave>.txt)."""

from pathlib import Path

from robo_nfce.extracao.linhas import CAMPOS_ITEM, CAMPOS_NFCE, aplicar_campos_nfce, expandir_por_itens
from robo_nfce.extracao.nfce import extrair_campos_nfce
from robo_nfce.utils.arquivos import listar_arquivos_texto
from robo_nfce.utils.csv_io import adicionar_colunas, escrever_csv, ler_csv

CAMPOS_SAIDA = ["chave", "arquivo_texto_capturado", *CAMPOS_NFCE, *CAMPOS_ITEM]


def carregar_textos_por_chave(entrada: Path) -> dict[str, dict]:
    """Le cada .txt e indexa pela chave (nome do arquivo ou chave encontrada no texto)."""
    textos = {}
    for arquivo in listar_arquivos_texto(entrada):
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        campos_nfce = extrair_campos_nfce(texto)
        chave_texto = (campos_nfce.get("chave") or "").strip()
        chave = arquivo.stem.strip() or chave_texto
        if not chave:
            continue
        if not chave_texto:
            campos_nfce["chave"] = chave

        textos[chave] = {"arquivo": arquivo, "texto": texto, "campos_nfce": campos_nfce}
    return textos


def _linhas_atualizadas(linha: dict, campos_nfce: dict, caminho_texto: Path | None) -> list[dict]:
    linha["chave"] = campos_nfce.get("chave") or linha.get("chave", "")
    if caminho_texto:
        linha["arquivo_texto_capturado"] = str(caminho_texto)
    aplicar_campos_nfce(linha, campos_nfce)
    return expandir_por_itens(linha, campos_nfce["itens"])


def gerar_csv_de_textos_capturados(entrada: Path, saida: Path, delimitador: str = ",") -> int:
    textos_por_chave = carregar_textos_por_chave(entrada)
    linhas_saida = []
    for chave in sorted(textos_por_chave):
        dados = textos_por_chave[chave]
        linhas_saida.extend(_linhas_atualizadas({"chave": chave}, dados["campos_nfce"], dados["arquivo"]))

    escrever_csv(saida, list(CAMPOS_SAIDA), linhas_saida, delimitador)
    return len(textos_por_chave)


def atualizar_csv_existente_com_textos(
    *,
    entrada_csv: Path,
    saida: Path,
    pasta_textos: Path,
    delimitador: str = ",",
    somente_sem_itens: bool = False,
) -> int:
    """Recalcula os campos de NFC-e das chaves que tiverem .txt; demais linhas ficam intactas."""
    textos_por_chave = carregar_textos_por_chave(pasta_textos)
    fieldnames_entrada, linhas_entrada = ler_csv(entrada_csv, delimitador)
    fieldnames_saida = adicionar_colunas(fieldnames_entrada, CAMPOS_SAIDA)

    grupos: dict[str, list[dict]] = {}
    for linha in linhas_entrada:
        grupos.setdefault((linha.get("chave") or "").strip(), []).append(linha)

    linhas_saida = []
    chaves_atualizadas = 0
    for chave, grupo in grupos.items():
        texto_disponivel = textos_por_chave.get(chave)
        representante = grupo[0]
        ja_tem_itens = (representante.get("tem_itens") or "").strip().lower() != "nao"

        if not texto_disponivel or (somente_sem_itens and ja_tem_itens):
            linhas_saida.extend(grupo)
            continue

        linhas_saida.extend(
            _linhas_atualizadas(dict(representante), texto_disponivel["campos_nfce"], texto_disponivel["arquivo"])
        )
        chaves_atualizadas += 1

    escrever_csv(saida, fieldnames_saida, linhas_saida, delimitador)
    return chaves_atualizadas
