"""Aplicacao dos campos extraidos da NFC-e nas linhas do CSV."""

CAMPOS_NFCE = [
    "nota_numero",
    "nota_emissao",
    "tem_itens",
    "tem_combustivel",
    "combustiveis",
    "litros_total",
    "valor_itens_combustivel",
]

CAMPOS_ITEM = [
    "item_descricao",
    "item_qtde",
    "item_un",
    "item_vl_unit",
    "item_vl_total",
]


def aplicar_campos_nfce(linha: dict, campos_nfce: dict) -> dict:
    for campo in CAMPOS_NFCE:
        linha[campo] = campos_nfce.get(campo, "")
    return linha


def expandir_por_itens(linha_base: dict, itens: list[dict]) -> list[dict]:
    """Gera uma linha por item; sem itens, retorna uma unica linha com campos de item vazios."""
    if not itens:
        return [_com_item(linha_base, {})]
    return [_com_item(linha_base, item) for item in itens]


def _com_item(linha_base: dict, item: dict) -> dict:
    linha = dict(linha_base)
    for campo in CAMPOS_ITEM:
        linha[campo] = item.get(campo, "")
    return linha
