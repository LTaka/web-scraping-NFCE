"""Conversao de valores no formato brasileiro (1.234,56)."""

from decimal import Decimal


def br_decimal(valor: str) -> Decimal:
    if not valor:
        return Decimal("0")
    return Decimal(valor.replace(".", "").replace(",", "."))


def decimal_br(valor: Decimal) -> str:
    return f"{valor:.3f}".replace(".", ",")


def dinheiro_br(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")


def normalizar_dinheiro_br(valor: str) -> str:
    if not valor:
        return ""
    return dinheiro_br(br_decimal(valor))


def formatar_decimal_compacto(valor: Decimal) -> str:
    """Formata sem zeros a direita: Decimal('10.500') -> '10,5'."""
    texto = format(valor.normalize(), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")
