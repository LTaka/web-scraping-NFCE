"""Selecao de arquivos SPED (.txt, .zip ou pasta) e conversao para o CSV base."""

import re
from pathlib import Path

from robo_nfce.sped.modelos import CAMPOS_CSV_BASE, NotaC100
from robo_nfce.sped.parser import parse_sped
from robo_nfce.utils.arquivos import limpar_txt_filtrados, listar_arquivos_texto, preparar_entrada_txt
from robo_nfce.utils.csv_io import escrever_csv

PADRAO_NOME_SPED = re.compile(
    r"^(?P<tipo_arquivo>[A-Z0-9]+)_"
    r"(?P<periodo_inicial>\d{8})_"
    r"(?P<periodo_final>\d{8})_"
    r"(?P<cnpj>\d{14})_"
    r"(?P<tipo_entrega>Original|Retificadora)_"
    r"(?P<data_entrega>\d{14})_"
    r"(?P<hash>[A-Fa-f0-9]+)$"
)


def resolver_arquivo_entrada(caminho: str) -> Path:
    arquivo = Path(caminho)
    if arquivo.exists():
        return arquivo

    if arquivo.name.endswith(".txt.txt"):
        candidato = arquivo.with_name(arquivo.name[:-4])
        if candidato.exists():
            return candidato

    raise FileNotFoundError(
        f"Arquivo nao encontrado: {arquivo}. "
        "Verifique o nome informado. Se o arquivo terminar com '.txt', "
        "evite repetir a extensao como '.txt.txt'."
    )


def analisar_nome_arquivo_sped(arquivo: Path) -> dict | None:
    match = PADRAO_NOME_SPED.match(arquivo.stem)
    return match.groupdict() if match else None


def selecionar_arquivos_txt_por_periodo(arquivos: list[Path]) -> list[Path]:
    """Para cada (tipo, periodo, CNPJ) mantem apenas a entrega mais antiga.

    Arquivos fora do padrao de nome sao sempre mantidos.
    """
    grupos: dict[tuple, tuple[dict, Path]] = {}
    arquivos_sem_padrao = []

    for arquivo in arquivos:
        metadados = analisar_nome_arquivo_sped(arquivo)
        if not metadados:
            arquivos_sem_padrao.append(arquivo)
            continue

        chave_grupo = (
            metadados["tipo_arquivo"],
            metadados["periodo_inicial"],
            metadados["periodo_final"],
            metadados["cnpj"],
        )
        atual = grupos.get(chave_grupo)
        if not atual or metadados["data_entrega"] < atual[0]["data_entrega"]:
            grupos[chave_grupo] = (metadados, arquivo)

    return sorted([arquivo for _, arquivo in grupos.values()] + arquivos_sem_padrao)


def _filtrar_nomes_por_periodo(nomes: list[str]) -> set[str]:
    return {arquivo.name for arquivo in selecionar_arquivos_txt_por_periodo([Path(nome) for nome in nomes])}


def deduplicar_notas_por_chave(notas: list[NotaC100]) -> list[NotaC100]:
    """Mantem a primeira ocorrencia de cada chave (notas sem chave sao mantidas)."""
    vistos = set()
    resultado = []
    for nota in notas:
        chave = (nota.chave or "").strip()
        if chave:
            if chave in vistos:
                continue
            vistos.add(chave)
        resultado.append(nota)
    return resultado


def carregar_notas_de_entrada(entrada: Path) -> list[NotaC100]:
    notas = []
    for arquivo in listar_arquivos_texto(entrada):
        notas.extend(parse_sped(arquivo))
    return deduplicar_notas_por_chave(notas)


def gerar_csv_base_do_sped(
    entrada: str,
    saida: Path,
    delimitador: str = ",",
    pasta_txt_filtrados: Path | None = None,
) -> int:
    """Converte SPED (.txt, .zip ou pasta) no CSV base do robo. Retorna o total de notas."""
    entrada_original = resolver_arquivo_entrada(entrada)
    entrada_preparada, _ = preparar_entrada_txt(
        entrada_original,
        pasta_txt_filtrados,
        filtro_nomes=_filtrar_nomes_por_periodo,
    )
    try:
        notas = carregar_notas_de_entrada(entrada_preparada)
        escrever_csv(saida, CAMPOS_CSV_BASE, (nota.to_row() for nota in notas), delimitador)
    finally:
        if entrada_original.suffix.lower() == ".zip":
            limpar_txt_filtrados(entrada_preparada)
    return len(notas)
