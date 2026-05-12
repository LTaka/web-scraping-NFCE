import argparse
import csv
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path


CAMPOS_SAIDA = [
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

COMBUSTIVEIS = [
    "GASOLINA",
    "DIESEL",
    "ETANOL",
    "ALCOOL",
    "ÁLCOOL",
    "GNV",
]

COD_SIT_PERMITIDOS = {"00", "01", "0"}


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
        itens_combustivel = [
            item for item in self.itens
            if eh_combustivel(item.descricao)
        ]
        combustiveis = sorted({
            limpar_descricao_combustivel(item.descricao)
            for item in itens_combustivel
        })
        litros_total = sum(
            item.quantidade
            for item in itens_combustivel
            if item.unidade.upper() == "L"
        )
        valor_combustivel = sum(
            (item.valor_item for item in itens_combustivel),
            Decimal("0"),
        )

        return {
            "chave": self.chave,
            "numero": self.numero,
            "serie": self.serie,
            "cod_sit": self.cod_sit,
            "data": self.data,
            "valor_total": formatar_decimal(self.valor_total),
            "tem_itens": "sim" if self.itens else "nao",
            "tem_combustivel": "sim" if itens_combustivel else "nao",
            "combustiveis": " | ".join(combustiveis),
            "litros_total": formatar_decimal(litros_total) if itens_combustivel else "",
            "valor_itens_combustivel": formatar_decimal(valor_combustivel) if itens_combustivel else "",
        }


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
                continue

            if registro == "C170" and nota_atual is not None:
                item = parse_c170(partes)
                if item is not None:
                    nota_atual.itens.append(item)

    return notas


def parse_c100(partes: list[str]) -> NotaC100 | None:
    if len(partes) < 13:
        return None

    cod_mod = partes[5]
    cod_sit = partes[6].strip()
    if cod_mod != "65":
        return None
    if cod_sit not in COD_SIT_PERMITIDOS:
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


def formatar_decimal(valor: Decimal) -> str:
    texto = format(valor.normalize(), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def formatar_data_sped(valor: str) -> str:
    if not valor:
        return ""
    return datetime.strptime(valor, "%d%m%Y").strftime("%Y-%m-%d")


def eh_combustivel(descricao: str) -> bool:
    descricao = descricao.upper()
    return any(nome in descricao for nome in COMBUSTIVEIS)


def limpar_descricao_combustivel(descricao: str) -> str:
    return " ".join(descricao.split()).strip()


def escrever_csv(notas: list[NotaC100], arquivo_saida: Path, delimitador: str) -> None:
    with arquivo_saida.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=CAMPOS_SAIDA, delimiter=delimitador)
        writer.writeheader()
        for nota in notas:
            writer.writerow(nota.to_row())


def resolver_arquivo_entrada(caminho: str) -> Path:
    arquivo = Path(caminho)
    if arquivo.exists():
        return arquivo

    nome = arquivo.name
    if nome.endswith(".txt.txt"):
        candidato = arquivo.with_name(nome[:-4])
        if candidato.exists():
            return candidato

    raise FileNotFoundError(
        f"Arquivo nao encontrado: {arquivo}. "
        "Verifique o nome informado. Se o arquivo terminar com '.txt', "
        "evite repetir a extensao como '.txt.txt'."
    )


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Le um arquivo SPED EFD e gera um CSV com notas C100 de modelo 65.",
    )
    parser.add_argument("entrada", help="Caminho do arquivo SPED.")
    parser.add_argument(
        "--saida",
        default="exemplo_entrada.csv",
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
    notas = parse_sped(resolver_arquivo_entrada(args.entrada))
    escrever_csv(notas, Path(args.saida), args.delimitador)
