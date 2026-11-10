"""Leitura dos registros C100 (modelo 65) e C170 de um arquivo SPED EFD."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from robo_nfce.sped.modelos import ItemC170, NotaC100

MODELO_NFCE = "65"
COD_SIT_PERMITIDOS = {"00", "01", "0"}


def parse_sped(arquivo: Path) -> list[NotaC100]:
    notas: list[NotaC100] = []
    nota_atual: NotaC100 | None = None

    with arquivo.open("r", encoding="utf-8", errors="ignore") as fp:
        for linha in fp:
            linha = linha.strip()
            if not linha.startswith("|"):
                continue

            partes = linha.split("|")
            if len(partes) < 3:
                continue

            registro = partes[1]
            if registro == "C100":
                nota_atual = parse_c100(partes)
                if nota_atual is not None:
                    notas.append(nota_atual)
            elif registro == "C170" and nota_atual is not None:
                item = parse_c170(partes)
                if item is not None:
                    nota_atual.itens.append(item)

    return notas


def parse_c100(partes: list[str]) -> NotaC100 | None:
    if len(partes) < 13:
        return None

    cod_mod = partes[5]
    cod_sit = partes[6].strip()
    if cod_mod != MODELO_NFCE or cod_sit not in COD_SIT_PERMITIDOS:
        return None

    return NotaC100(
        chave=partes[9].strip(),
        numero=partes[8].strip(),
        serie=partes[7].strip(),
        cod_sit=cod_sit,
        data=formatar_data_sped(partes[10].strip()),
        valor_total=parse_decimal(partes[12]),
    )


def parse_c170(partes: list[str]) -> ItemC170 | None:
    if len(partes) < 8:
        return None

    descricao = partes[4].strip()
    if not descricao:
        return None

    return ItemC170(
        descricao=descricao,
        quantidade=parse_decimal(partes[6]),
        unidade=partes[7].strip(),
        valor_item=parse_decimal(partes[8] if len(partes) > 8 else ""),
    )


def parse_decimal(valor: str) -> Decimal:
    valor = (valor or "").strip()
    if not valor:
        return Decimal("0")
    return Decimal(valor.replace(".", "").replace(",", "."))


def formatar_data_sped(valor: str) -> str:
    """'31052021' -> '2021-05-31'."""
    if not valor:
        return ""
    return datetime.strptime(valor, "%d%m%Y").strftime("%Y-%m-%d")
