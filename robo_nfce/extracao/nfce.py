"""Extracao dos dados da NFC-e a partir do texto copiado da pagina de consulta."""

import re

from robo_nfce.extracao.combustivel import eh_item_combustivel, limpar_descricao_combustivel
from robo_nfce.extracao.formatacao import br_decimal, decimal_br, dinheiro_br, normalizar_dinheiro_br
from robo_nfce.utils.texto import normalizar_quebras

PADRAO_VALOR = r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}"
PADRAO_QTDE = r"\d+(?:[.,]\d+)*"

PADROES_NUMERO_NOTA = [
    r"Numero:\s*([0-9.\-\/]+)",
    r"Numero\s*([0-9.\-\/]+)",
    r"N[uú]mero:\s*([0-9.\-\/]+)",
    r"N[uú]mero\s*([0-9.\-\/]+)",
    r"Modelo\s+S[ée]rie\s+N[uú]mero\s+Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+([0-9]+)\s+[0-9]{2}/[0-9]{2}/[0-9]{4}",
]

PADROES_EMISSAO = [
    r"Emissao:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
    r"Emiss[aã]o:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
    r"Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+\d+\s+([0-9]{2}/[0-9]{2}/[0-9]{4}\s+[0-9:]{8})",
]


def extrair_campos_nfce(texto: str) -> dict:
    """Retorna chave, numero, emissao, itens e resumo de combustivel da NFC-e."""
    texto = texto or ""
    itens = extrair_itens(texto)

    itens_combustivel = [
        item for item in itens
        if eh_item_combustivel(item.get("item_descricao", ""), item.get("item_un", ""))
    ]
    litros_total = sum(
        br_decimal(item.get("item_qtde", "0"))
        for item in itens_combustivel
        if item.get("item_un", "").upper() == "L"
    )
    valor_combustivel = sum(br_decimal(item.get("item_vl_total", "0")) for item in itens_combustivel)
    combustiveis = sorted({limpar_descricao_combustivel(item["item_descricao"]) for item in itens_combustivel})

    return {
        "chave": extrair_chave_acesso(texto),
        "nota_numero": _extrair_primeiro(texto, PADROES_NUMERO_NOTA),
        "nota_emissao": _extrair_primeiro(texto, PADROES_EMISSAO),
        "itens": itens,
        "tem_itens": "sim" if itens else "nao",
        "tem_combustivel": "sim" if itens_combustivel else "nao",
        "combustiveis": " | ".join(combustiveis),
        "litros_total": decimal_br(litros_total) if itens_combustivel else "",
        "valor_itens_combustivel": dinheiro_br(valor_combustivel) if itens_combustivel else "",
    }


def extrair_chave_acesso(texto: str) -> str:
    match = re.search(r"Chave\s+de\s+acesso[:\s]*([0-9.\-\/\s]+)", texto, flags=re.IGNORECASE)
    if not match:
        return ""
    digitos = re.sub(r"\D", "", match.group(1))
    return digitos if len(digitos) == 44 else ""


def extrair_itens(texto: str) -> list[dict]:
    """Tenta, em ordem: tabela MG, blocos 'Vl. Total' (ES/RJ) e texto corrido."""
    texto_normalizado = normalizar_quebras(texto)

    itens = _extrair_itens_tabela_mg(texto_normalizado)
    if itens:
        return _deduplicar_itens(itens)

    itens = _extrair_itens_por_bloco(texto_normalizado)
    if itens:
        return _deduplicar_itens(itens)

    return _extrair_itens_texto_corrido(texto_normalizado)


def _extrair_primeiro(texto: str, padroes: list[str]) -> str:
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split()).strip()
    return ""


def _extrair_itens_tabela_mg(texto: str) -> list[dict]:
    if "Produtos e Serviços" not in texto or "Valor(R$)" not in texto:
        return []

    padrao_item = re.compile(
        r"^\s*\d+\s+"
        r"(?P<descricao>.+?)\s+"
        rf"(?P<qtde>{PADRAO_QTDE})\s+"
        r"(?P<un>[A-Za-z]+)\s+"
        rf"R\$\s*(?P<vl_unit>{PADRAO_VALOR})\s+"
        rf"R\$\s*(?P<vl_total>{PADRAO_VALOR})\s*$"
    )

    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    capturando = False
    itens = []

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
            "item_vl_unit": normalizar_dinheiro_br(match.group("vl_unit")),
            "item_vl_total": normalizar_dinheiro_br(match.group("vl_total")),
        })

    return itens


def _extrair_itens_por_bloco(texto: str) -> list[dict]:
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    itens = []
    for indice, linha in enumerate(linhas):
        if "vl. total" not in linha.lower():
            continue
        bloco = " ".join(linhas[max(0, indice - 1): min(len(linhas), indice + 2)]).strip()
        item = _parse_bloco_item(bloco)
        if item:
            itens.append(item)
    return itens


def _parse_bloco_item(bloco: str) -> dict | None:
    bloco = " ".join(bloco.split())
    padrao_valor = rf"({PADRAO_VALOR})"

    total_match = re.search(rf"Vl\.\s*Total\s*{padrao_valor}", bloco, flags=re.IGNORECASE)
    if not total_match:
        return None

    qtd_match = re.search(r"Qtde\.:?\s*([0-9]+(?:,[0-9]+)?)", bloco, flags=re.IGNORECASE)
    un_match = re.search(r"UN:?\s*([A-Za-z]+)", bloco, flags=re.IGNORECASE)
    unit_match = re.search(rf"Vl\.\s*Unit\.:?\s*{padrao_valor}", bloco, flags=re.IGNORECASE)

    descricao = re.sub(r"\(C[oó]digo:.*?\)", "", bloco, flags=re.IGNORECASE)
    descricao = re.sub(r"Qtde\.:?.*$", "", descricao, flags=re.IGNORECASE).strip(" -:")
    if not descricao:
        return None

    return {
        "item_descricao": descricao.strip(),
        "item_qtde": qtd_match.group(1) if qtd_match else "",
        "item_un": un_match.group(1) if un_match else "",
        "item_vl_unit": normalizar_dinheiro_br(unit_match.group(1)) if unit_match else "",
        "item_vl_total": normalizar_dinheiro_br(total_match.group(1)),
    }


def _extrair_itens_texto_corrido(texto: str) -> list[dict]:
    padrao = re.compile(
        r"(?P<descricao>[A-Z0-9][A-Z0-9\s./%-]{3,}?)"
        r"(?:\s*\(C[oó]digo:.*?\))?"
        rf"\s*Qtde\.:?\s*(?P<qtde>{PADRAO_QTDE})"
        r"\s*UN:?\s*(?P<un>[A-Za-z]+)"
        rf"\s*Vl\.\s*Unit\.:?\s*(?P<vl_unit>{PADRAO_VALOR})"
        rf"\s*Vl\.\s*Total\s*(?P<vl_total>{PADRAO_VALOR})",
        flags=re.IGNORECASE,
    )

    itens = [
        {
            "item_descricao": " ".join(match.group("descricao").split()).strip(" -:"),
            "item_qtde": match.group("qtde"),
            "item_un": match.group("un"),
            "item_vl_unit": normalizar_dinheiro_br(match.group("vl_unit")),
            "item_vl_total": normalizar_dinheiro_br(match.group("vl_total")),
        }
        for match in padrao.finditer(" ".join(texto.split()))
    ]
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
