import argparse
import csv
import re
import zipfile
from decimal import Decimal
from pathlib import Path

from ler_sped_c100 import CAMPOS_SAIDA as CAMPOS_SAIDA_SPED
from ler_sped_c100 import parse_sped


COMBUSTIVEIS = [
    "GASOLINA",
    "DIESEL",
    "ETANOL",
    "ALCOOL",
    "ÁLCOOL",
    "GNV",
]

CAMPOS_SAIDA = [
    "chave",
    "uf",
    "url_consulta",
    "arquivo_texto_capturado",
    "nota_numero",
    "nota_emissao",
    "tem_itens",
    "tem_combustivel",
    "combustiveis",
    "litros_total",
    "valor_itens_combustivel",
    "item_descricao",
    "item_qtde",
    "item_un",
    "item_vl_unit",
    "item_vl_total",
]

PADRAO_NOME_SPED = re.compile(
    r"^(?P<tipo_arquivo>[A-Z0-9]+)_"
    r"(?P<periodo_inicial>\d{8})_"
    r"(?P<periodo_final>\d{8})_"
    r"(?P<cnpj>\d{14})_"
    r"(?P<tipo_entrega>Original|Retificadora)_"
    r"(?P<data_entrega>\d{14})_"
    r"(?P<hash>[A-Fa-f0-9]+)$"
)


def br_decimal(valor: str) -> Decimal:
    if not valor:
        return Decimal("0")
    return Decimal(valor.replace(".", "").replace(",", "."))


def decimal_br(valor: Decimal) -> str:
    return f"{valor:.3f}".replace(".", ",")


def dinheiro_br(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")


def extrair_campos_nfce(texto: str) -> dict:
    texto = texto or ""
    itens = _extrair_itens(texto)
    chave_acesso = _extrair_chave_acesso(texto)

    itens_combustivel = [
        item for item in itens
        if _eh_combustivel(item.get("item_descricao", ""))
    ]

    litros_total = sum(
        br_decimal(item.get("item_qtde", "0"))
        for item in itens_combustivel
        if item.get("item_un", "").upper() == "L"
    )

    valor_combustivel = sum(
        br_decimal(item.get("item_vl_total", "0"))
        for item in itens_combustivel
    )

    combustiveis = sorted({
        _limpar_descricao_combustivel(item["item_descricao"])
        for item in itens_combustivel
    })

    return {
        "chave": chave_acesso,
        "nota_numero": _extrair_primeiro(texto, [
            r"Numero:\s*([0-9.\-\/]+)",
            r"Numero\s*([0-9.\-\/]+)",
            r"N[uú]mero:\s*([0-9.\-\/]+)",
            r"N[uú]mero\s*([0-9.\-\/]+)",
            r"Modelo\s+S[ée]rie\s+N[uú]mero\s+Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+([0-9]+)\s+[0-9]{2}/[0-9]{2}/[0-9]{4}",
        ]),
        "nota_emissao": _extrair_primeiro(texto, [
            r"Emissao:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
            r"Emiss[aã]o:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
            r"Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+\d+\s+([0-9]{2}/[0-9]{2}/[0-9]{4}\s+[0-9:]{8})",
        ]),
        "itens": itens,
        "tem_itens": "sim" if itens else "nao",
        "tem_combustivel": "sim" if itens_combustivel else "nao",
        "combustiveis": " | ".join(combustiveis),
        "litros_total": decimal_br(litros_total) if itens_combustivel else "",
        "valor_itens_combustivel": dinheiro_br(valor_combustivel) if itens_combustivel else "",
    }


def _eh_combustivel(descricao: str) -> bool:
    descricao = descricao.upper()
    return any(nome in descricao for nome in COMBUSTIVEIS)


def _limpar_descricao_combustivel(descricao: str) -> str:
    descricao = re.sub(r"\s*Bico\s+[0-9]+", "", descricao, flags=re.IGNORECASE)
    return " ".join(descricao.split()).strip()


def _extrair_primeiro(texto: str, padroes: list[str]) -> str:
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split()).strip()
    return ""


def _extrair_chave_acesso(texto: str) -> str:
    match = re.search(
        r"Chave\s+de\s+acesso:\s*([0-9\s]+)",
        texto,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    digitos = re.sub(r"\D", "", match.group(1))
    return digitos if len(digitos) == 44 else ""


def _extrair_itens(texto: str) -> list[dict]:
    texto_normalizado = _normalizar_quebras(texto)
    itens = _extrair_itens_tabela_mg(texto_normalizado)
    if itens:
        return _deduplicar_itens(itens)

    linhas = [linha.strip() for linha in texto_normalizado.splitlines() if linha.strip()]
    itens = []

    for indice, linha in enumerate(linhas):
        if "vl. total" not in linha.lower():
            continue

        bloco = " ".join(linhas[max(0, indice - 1): min(len(linhas), indice + 2)]).strip()
        item = _parse_bloco_item(bloco)
        if item:
            itens.append(item)

    if itens:
        return _deduplicar_itens(itens)

    return _extrair_itens_texto_corrido(texto_normalizado)


def _extrair_itens_tabela_mg(texto: str) -> list[dict]:
    if "Produtos e Serviços" not in texto or "Valor(R$)" not in texto:
        return []

    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    capturando = False
    itens = []
    padrao_item = re.compile(
        r"^\s*\d+\s+"
        r"(?P<descricao>.+?)\s+"
        r"(?P<qtde>\d+(?:[.,]\d+)?)\s+"
        r"(?P<un>[A-Za-z]+)\s+"
        r"R\$\s*(?P<vl_unit>\d+[.,]\d{2})\s+"
        r"R\$\s*(?P<vl_total>\d+[.,]\d{2})\s*$"
    )

    for linha in linhas:
        if "Número" in linha and "Valor(R$)" in linha:
            capturando = True
            continue

        if not capturando:
            continue

        if linha.startswith("Situação atual:") or linha.startswith("Versão "):
            break

        match = padrao_item.match(linha)
        if not match:
            continue

        itens.append({
            "item_numero": linha.split()[0],
            "item_descricao": " ".join(match.group("descricao").split()).strip(" -:"),
            "item_qtde": match.group("qtde").replace(".", ","),
            "item_un": match.group("un"),
            "item_vl_unit": match.group("vl_unit"),
            "item_vl_total": match.group("vl_total"),
        })

    return itens


def _parse_bloco_item(bloco: str) -> dict | None:
    bloco = " ".join(bloco.split())

    total_match = re.search(r"Vl\.\s*Total\s*([0-9]+,[0-9]{2})", bloco, flags=re.IGNORECASE)
    qtd_match = re.search(r"Qtde\.:?\s*([0-9]+(?:,[0-9]+)?)", bloco, flags=re.IGNORECASE)
    un_match = re.search(r"UN:?\s*([A-Za-z]+)", bloco, flags=re.IGNORECASE)
    unit_match = re.search(r"Vl\.\s*Unit\.:?\s*([0-9]+,[0-9]{2})", bloco, flags=re.IGNORECASE)

    if not total_match:
        return None

    descricao = bloco
    descricao = re.sub(r"\(C[oó]digo:.*?\)", "", descricao, flags=re.IGNORECASE)
    descricao = re.sub(r"Qtde\.:?.*$", "", descricao, flags=re.IGNORECASE).strip(" -:")

    if not descricao:
        return None

    return {
        "item_descricao": descricao.strip(),
        "item_qtde": qtd_match.group(1) if qtd_match else "",
        "item_un": un_match.group(1) if un_match else "",
        "item_vl_unit": unit_match.group(1) if unit_match else "",
        "item_vl_total": total_match.group(1),
    }


def _extrair_itens_texto_corrido(texto: str) -> list[dict]:
    padrao = re.compile(
        r"(?P<descricao>[A-Z0-9][A-Z0-9\s./%-]{3,}?)"
        r"(?:\s*\(C[oó]digo:.*?\))?"
        r"\s*Qtde\.:?\s*(?P<qtde>[0-9]+(?:,[0-9]+)?)"
        r"\s*UN:?\s*(?P<un>[A-Za-z]+)"
        r"\s*Vl\.\s*Unit\.:?\s*(?P<vl_unit>[0-9]+,[0-9]{2})"
        r"\s*Vl\.\s*Total\s*(?P<vl_total>[0-9]+,[0-9]{2})",
        flags=re.IGNORECASE,
    )

    itens = []
    texto_corrido = " ".join(texto.split())

    for match in padrao.finditer(texto_corrido):
        itens.append({
            "item_descricao": " ".join(match.group("descricao").split()).strip(" -:"),
            "item_qtde": match.group("qtde"),
            "item_un": match.group("un"),
            "item_vl_unit": match.group("vl_unit"),
            "item_vl_total": match.group("vl_total"),
        })

    return _deduplicar_itens(itens)


def _deduplicar_itens(itens: list[dict]) -> list[dict]:
    vistos = set()
    resultado = []

    for item in itens:
        chave = (
            item.get("item_numero", ""),
            item.get("item_descricao", "").lower(),
            item.get("item_qtde", ""),
            item.get("item_un", "").lower(),
            item.get("item_vl_unit", ""),
            item.get("item_vl_total", ""),
        )
        if chave in vistos:
            continue

        vistos.add(chave)
        resultado.append(item)

    return resultado


def _normalizar_quebras(texto: str) -> str:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{2,}", "\n", texto)


def analisar_nome_arquivo_sped(arquivo: Path) -> dict | None:
    match = PADRAO_NOME_SPED.match(arquivo.stem)
    if not match:
        return None
    return match.groupdict()


def selecionar_arquivos_txt_por_periodo(arquivos: list[Path]) -> list[Path]:
    grupos = {}
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

    arquivos_selecionados = [item[1] for item in grupos.values()]
    arquivos_selecionados.extend(arquivos_sem_padrao)
    return sorted(arquivos_selecionados)


def extrair_txts_selecionados_de_zip(arquivo_zip: Path, pasta_saida: Path) -> list[Path]:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    for arquivo_existente in pasta_saida.glob("*.txt"):
        if arquivo_existente.is_file():
            arquivo_existente.unlink()

    with zipfile.ZipFile(arquivo_zip) as zip_ref:
        membros_txt = [
            info for info in zip_ref.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".txt")
        ]
        nomes = [Path(info.filename).name for info in membros_txt]
        caminhos_temporarios = [Path(nome) for nome in nomes]
        nomes_selecionados = {
            arquivo.name
            for arquivo in selecionar_arquivos_txt_por_periodo(caminhos_temporarios)
        }

        arquivos_extraidos = []
        for info in membros_txt:
            nome_arquivo = Path(info.filename).name
            if nome_arquivo not in nomes_selecionados:
                continue

            destino = pasta_saida / nome_arquivo
            with zip_ref.open(info) as origem, destino.open("wb") as saida:
                saida.write(origem.read())
            arquivos_extraidos.append(destino)

    return sorted(arquivos_extraidos)


def gerar_linhas_csv_de_arquivo(arquivo_texto: Path) -> list[dict[str, str]]:
    notas = parse_sped(arquivo_texto)
    return [nota.to_row() for nota in notas]


def listar_arquivos_texto(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(arquivo for arquivo in entrada.glob("*.txt") if arquivo.is_file())


def preparar_entrada_txt(entrada: Path, pasta_txt_filtrados: Path | None = None) -> tuple[Path, int]:
    if entrada.is_file() and entrada.suffix.lower() == ".zip":
        if pasta_txt_filtrados is None:
            pasta_txt_filtrados = entrada.with_name(f"{entrada.stem}_txt_filtrados")
        arquivos_extraidos = extrair_txts_selecionados_de_zip(entrada, pasta_txt_filtrados)
        return pasta_txt_filtrados, len(arquivos_extraidos)

    arquivos = listar_arquivos_texto(entrada)
    return entrada, len(arquivos)


def limpar_txt_filtrados(pasta_txt_filtrados: Path) -> None:
    if not pasta_txt_filtrados.exists() or not pasta_txt_filtrados.is_dir():
        return

    for arquivo in pasta_txt_filtrados.glob("*.txt"):
        if arquivo.is_file():
            arquivo.unlink()

    try:
        pasta_txt_filtrados.rmdir()
    except OSError:
        pass


def gerar_csv_de_textos_capturados(entrada: Path, saida: Path, delimitador: str) -> int:
    arquivos = listar_arquivos_texto(entrada)
    linhas_saida = []

    for arquivo in arquivos:
        linhas_saida.extend(gerar_linhas_csv_de_arquivo(arquivo))

    with saida.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=CAMPOS_SAIDA_SPED, delimiter=delimitador)
        writer.writeheader()
        writer.writerows(linhas_saida)

    return len(arquivos)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Le arquivos .txt capturados de NFC-e e gera um CSV com os campos extraidos.",
    )
    parser.add_argument(
        "entrada",
        help="Arquivo .txt, arquivo .zip ou pasta com os textos capturados.",
    )
    parser.add_argument(
        "--saida",
        default="resultado.csv",
        help="Caminho do CSV de saida.",
    )
    parser.add_argument(
        "--delimitador",
        default=",",
        help="Delimitador do CSV de saida.",
    )
    parser.add_argument(
        "--pasta-txt-filtrados",
        default=None,
        help="Pasta usada para salvar os .txt selecionados quando a entrada for um .zip.",
    )
    return parser


if __name__ == "__main__":
    args = criar_parser().parse_args()
    entrada_original = Path(args.entrada)
    entrada_preparada, _ = preparar_entrada_txt(
        entrada=entrada_original,
        pasta_txt_filtrados=Path(args.pasta_txt_filtrados) if args.pasta_txt_filtrados else None,
    )
    quantidade = gerar_csv_de_textos_capturados(
        entrada=entrada_preparada,
        saida=Path(args.saida),
        delimitador=args.delimitador,
    )
    if entrada_original.suffix.lower() == ".zip":
        limpar_txt_filtrados(entrada_preparada)
    print(f"CSV gerado com {quantidade} arquivo(s): {args.saida}")
