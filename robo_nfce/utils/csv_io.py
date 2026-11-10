import csv
from pathlib import Path
from typing import Iterable


def ler_csv(caminho: Path, delimitador: str = ",") -> tuple[list[str], list[dict]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError(f"O CSV {caminho} precisa ter cabecalho.")
        return list(leitor.fieldnames), list(leitor)


def escrever_csv(caminho: Path, fieldnames: list[str], linhas: Iterable[dict], delimitador: str = ",") -> None:
    """Grava as linhas mantendo apenas as colunas de `fieldnames` (faltantes viram "")."""
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=fieldnames, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows({campo: linha.get(campo, "") for campo in fieldnames} for linha in linhas)


def adicionar_colunas(fieldnames: list[str] | None, colunas_extras: list[str]) -> list[str]:
    """Mantem a ordem original e acrescenta as colunas extras que ainda nao existem."""
    resultado = list(fieldnames or [])
    for coluna in colunas_extras:
        if coluna not in resultado:
            resultado.append(coluna)
    return resultado
