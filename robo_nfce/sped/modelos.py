from dataclasses import dataclass, field
from decimal import Decimal

from robo_nfce.extracao.combustivel import descricao_tem_combustivel
from robo_nfce.extracao.formatacao import formatar_decimal_compacto

CAMPOS_CSV_BASE = [
    "chave",
    "numero",
    "serie",
    "cod_sit",
    "data",
    "valor_total",
    "tem_itens",
    "tem_combustivel",
    "combustiveis",
    "litros_total",
    "valor_itens_combustivel",
]


@dataclass
class ItemC170:
    descricao: str
    quantidade: Decimal
    unidade: str
    valor_item: Decimal


@dataclass
class NotaC100:
    chave: str
    numero: str
    serie: str
    cod_sit: str
    data: str
    valor_total: Decimal
    itens: list[ItemC170] = field(default_factory=list)

    def to_row(self) -> dict[str, str]:
        itens_combustivel = [item for item in self.itens if descricao_tem_combustivel(item.descricao)]
        combustiveis = sorted({" ".join(item.descricao.split()) for item in itens_combustivel})
        litros_total = sum(
            (item.quantidade for item in itens_combustivel if item.unidade.upper() == "L"),
            Decimal("0"),
        )
        valor_combustivel = sum((item.valor_item for item in itens_combustivel), Decimal("0"))

        return {
            "chave": self.chave,
            "numero": self.numero,
            "serie": self.serie,
            "cod_sit": self.cod_sit,
            "data": self.data,
            "valor_total": formatar_decimal_compacto(self.valor_total),
            "tem_itens": "sim" if self.itens else "nao",
            "tem_combustivel": "sim" if itens_combustivel else "nao",
            "combustiveis": " | ".join(combustiveis),
            "litros_total": formatar_decimal_compacto(litros_total) if itens_combustivel else "",
            "valor_itens_combustivel": formatar_decimal_compacto(valor_combustivel) if itens_combustivel else "",
        }
