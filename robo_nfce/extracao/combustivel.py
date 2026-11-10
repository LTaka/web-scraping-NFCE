"""Regras para identificar itens de combustivel."""

import re

COMBUSTIVEIS = (
    "GASOLINA",
    "DIESEL",
    "ETANOL",
    "ALCOOL",
    "ÁLCOOL",
    "GNV",
)

UNIDADES_COMBUSTIVEL = (
    "L",
    "LT",
    "LTS",
    "LITRO",
    "LITROS",
    "M3",
    "M³",
)


def descricao_tem_combustivel(descricao: str) -> bool:
    descricao = descricao.upper()
    return any(nome in descricao for nome in COMBUSTIVEIS)


def eh_item_combustivel(descricao: str, unidade: str) -> bool:
    """Combustivel = descricao com nome de combustivel E unidade de volume.

    Evita classificar, por exemplo, "FILTRO GASOLINA" (unidade Un) como combustivel.
    """
    return unidade.upper().strip() in UNIDADES_COMBUSTIVEL and descricao_tem_combustivel(descricao)


def limpar_descricao_combustivel(descricao: str) -> str:
    descricao = re.sub(r"\s*Bico\s+[0-9]+", "", descricao, flags=re.IGNORECASE)
    return " ".join(descricao.split()).strip()
