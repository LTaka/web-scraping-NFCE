import argparse
import csv
import re
from decimal import Decimal
from pathlib import Path

from config_ufs import obter_config_por_chave


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
        ]),
        "nota_emissao": _extrair_primeiro(texto, [
            r"Emissao:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
            r"Emiss[aã]o:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
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


def gerar_linhas_csv_de_arquivo(arquivo_texto: Path) -> list[dict[str, str]]:
    texto = arquivo_texto.read_text(encoding="utf-8", errors="ignore")
    campos_nfce = extrair_campos_nfce(texto)
    chave = campos_nfce["chave"] or arquivo_texto.stem
    itens = campos_nfce["itens"]

    linha_base = {
        "chave": chave,
        "uf": "",
        "url_consulta": "",
        "arquivo_texto_capturado": str(arquivo_texto),
        "nota_numero": campos_nfce["nota_numero"],
        "nota_emissao": campos_nfce["nota_emissao"],
        "tem_itens": campos_nfce["tem_itens"],
        "tem_combustivel": campos_nfce["tem_combustivel"],
        "combustiveis": campos_nfce["combustiveis"],
        "litros_total": campos_nfce["litros_total"],
        "valor_itens_combustivel": campos_nfce["valor_itens_combustivel"],
        "item_descricao": "",
        "item_qtde": "",
        "item_un": "",
        "item_vl_unit": "",
        "item_vl_total": "",
    }

    try:
        config = obter_config_por_chave(chave)
        linha_base["uf"] = config.uf
        linha_base["url_consulta"] = config.url
    except Exception:
        pass

    if not itens:
        return [linha_base]

    linhas = []
    for item in itens:
        linha = dict(linha_base)
        linha["item_descricao"] = item.get("item_descricao", "")
        linha["item_qtde"] = item.get("item_qtde", "")
        linha["item_un"] = item.get("item_un", "")
        linha["item_vl_unit"] = item.get("item_vl_unit", "")
        linha["item_vl_total"] = item.get("item_vl_total", "")
        linhas.append(linha)

    return linhas


def listar_arquivos_texto(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(arquivo for arquivo in entrada.glob("*.txt") if arquivo.is_file())


def gerar_csv_de_textos_capturados(entrada: Path, saida: Path, delimitador: str) -> int:
    arquivos = listar_arquivos_texto(entrada)
    linhas_saida = []

    for arquivo in arquivos:
        linhas_saida.extend(gerar_linhas_csv_de_arquivo(arquivo))

    with saida.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=CAMPOS_SAIDA, delimiter=delimitador)
        writer.writeheader()
        writer.writerows(linhas_saida)

    return len(arquivos)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Le arquivos .txt capturados de NFC-e e gera um CSV com os campos extraidos.",
    )
    parser.add_argument(
        "entrada",
        help="Arquivo .txt ou pasta com os textos capturados.",
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
    return parser


if __name__ == "__main__":
    args = criar_parser().parse_args()
    quantidade = gerar_csv_de_textos_capturados(
        entrada=Path(args.entrada),
        saida=Path(args.saida),
        delimitador=args.delimitador,
    )
    print(f"CSV gerado com {quantidade} arquivo(s): {args.saida}")
