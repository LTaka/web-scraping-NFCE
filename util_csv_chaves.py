import argparse
import csv
from pathlib import Path


def ler_csv(caminho: Path, delimitador: str) -> tuple[list[str], list[dict]]:
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError(f"O CSV {caminho} precisa ter cabecalho.")
        return list(leitor.fieldnames), list(leitor)


def escrever_csv(caminho: Path, fieldnames: list[str], linhas: list[dict], delimitador: str) -> None:
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=fieldnames, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows([{campo: linha.get(campo, "") for campo in fieldnames} for linha in linhas])


def filtrar_linhas_sem_itens_e_sem_combustivel(linhas: list[dict]) -> list[dict]:
    linhas_filtradas = []
    for linha in linhas:
        tem_itens = (linha.get("tem_itens") or "").strip().lower()
        tem_combustivel = (linha.get("tem_combustivel") or "").strip().lower()
        if tem_itens == "nao" and tem_combustivel == "nao":
            linhas_filtradas.append(linha)
    return linhas_filtradas


def dividir_lista_ao_meio(linhas: list[dict]) -> tuple[list[dict], list[dict]]:
    metade = (len(linhas) + 1) // 2
    return linhas[:metade], linhas[metade:]


def dividir_csv_filtrado(
    entrada: Path,
    saida_1: Path,
    saida_2: Path,
    delimitador: str = ",",
) -> tuple[int, int, int]:
    fieldnames, linhas = ler_csv(entrada, delimitador)
    linhas_filtradas = filtrar_linhas_sem_itens_e_sem_combustivel(linhas)
    linhas_1, linhas_2 = dividir_lista_ao_meio(linhas_filtradas)

    escrever_csv(saida_1, fieldnames, linhas_1, delimitador)
    escrever_csv(saida_2, fieldnames, linhas_2, delimitador)
    return len(linhas_filtradas), len(linhas_1), len(linhas_2)


def coletar_chaves(linhas: list[dict], coluna_chave: str) -> set[str]:
    chaves = set()
    for linha in linhas:
        chave = (linha.get(coluna_chave) or "").strip()
        if chave:
            chaves.add(chave)
    return chaves


def comparar_chaves_csv(
    csv_base: Path,
    csv_comparacao: Path,
    saida: Path,
    delimitador: str = ",",
    coluna_chave: str = "chave",
) -> dict[str, int]:
    _, linhas_base = ler_csv(csv_base, delimitador)
    _, linhas_comparacao = ler_csv(csv_comparacao, delimitador)

    chaves_base = coletar_chaves(linhas_base, coluna_chave)
    chaves_comparacao = coletar_chaves(linhas_comparacao, coluna_chave)
    todas_as_chaves = sorted(chaves_base | chaves_comparacao)

    linhas_saida = []
    faltando_no_base = 0
    faltando_no_comparacao = 0
    presentes_nos_dois = 0

    for chave in todas_as_chaves:
        esta_no_base = chave in chaves_base
        esta_no_comparacao = chave in chaves_comparacao

        if esta_no_base and esta_no_comparacao:
            status = "presente_nos_dois"
            presentes_nos_dois += 1
        elif esta_no_base:
            status = "faltando_no_arquivo_2"
            faltando_no_comparacao += 1
        else:
            status = "faltando_no_arquivo_1"
            faltando_no_base += 1

        linhas_saida.append(
            {
                coluna_chave: chave,
                "status_comparacao": status,
                "presente_arquivo_1": "sim" if esta_no_base else "nao",
                "presente_arquivo_2": "sim" if esta_no_comparacao else "nao",
            }
        )

    escrever_csv(
        saida,
        [coluna_chave, "status_comparacao", "presente_arquivo_1", "presente_arquivo_2"],
        linhas_saida,
        delimitador,
    )

    return {
        "arquivo_1": len(chaves_base),
        "arquivo_2": len(chaves_comparacao),
        "presentes_nos_dois": presentes_nos_dois,
        "faltando_no_arquivo_1": faltando_no_base,
        "faltando_no_arquivo_2": faltando_no_comparacao,
    }


def gerar_analise_faltantes_da_base(
    csv_base: Path,
    csv_conferido: Path,
    saida: Path,
    delimitador: str = ",",
    coluna_chave: str = "chave",
) -> dict[str, int]:
    fieldnames_base, linhas_base = ler_csv(csv_base, delimitador)
    _, linhas_conferido = ler_csv(csv_conferido, delimitador)

    chaves_conferido = coletar_chaves(linhas_conferido, coluna_chave)
    chaves_vistas = set()
    linhas_saida = []

    for linha in linhas_base:
        chave = (linha.get(coluna_chave) or "").strip()
        if not chave or chave in chaves_vistas:
            continue
        chaves_vistas.add(chave)

        if chave in chaves_conferido:
            continue

        linhas_saida.append(dict(linha))

    escrever_csv(saida, fieldnames_base, linhas_saida, delimitador)

    return {
        "base": len(coletar_chaves(linhas_base, coluna_chave)),
        "conferido": len(chaves_conferido),
        "faltando_no_conferido": len(linhas_saida),
    }


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Filtra/divide CSVs e compara chaves entre arquivos.",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    parser_dividir = subparsers.add_parser(
        "dividir",
        help="Filtra linhas com tem_itens=nao e tem_combustivel=nao e divide em dois arquivos.",
    )
    parser_dividir.add_argument("entrada", help="CSV de entrada.")
    parser_dividir.add_argument("--saida-1", default="entrada_1.csv", help="Primeiro CSV de saida.")
    parser_dividir.add_argument("--saida-2", default="entrada_2.csv", help="Segundo CSV de saida.")
    parser_dividir.add_argument("--delimitador", default=",", help="Delimitador do CSV.")

    parser_comparar = subparsers.add_parser(
        "comparar",
        help="Compara as chaves entre dois CSVs e grava o resultado em outro CSV.",
    )
    parser_comparar.add_argument("arquivo_1", help="Primeiro CSV.")
    parser_comparar.add_argument("arquivo_2", help="Segundo CSV.")
    parser_comparar.add_argument("--saida", default="comparacao_chaves.csv", help="CSV de comparacao.")
    parser_comparar.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    parser_comparar.add_argument(
        "--coluna-chave",
        default="chave",
        help="Nome da coluna usada para comparar as chaves.",
    )

    parser_analise = subparsers.add_parser(
        "analisar-faltantes",
        help="Gera um CSV com as linhas da base que nao existem no arquivo conferido.",
    )
    parser_analise.add_argument("base", help="CSV principal, usado como base.")
    parser_analise.add_argument("conferido", help="CSV usado para conferencia.")
    parser_analise.add_argument("--saida", default="analise_faltantes.csv", help="CSV de analise.")
    parser_analise.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    parser_analise.add_argument(
        "--coluna-chave",
        default="chave",
        help="Nome da coluna usada para comparar as chaves.",
    )

    return parser


def main() -> None:
    args = criar_parser().parse_args()

    if args.comando == "dividir":
        total, total_1, total_2 = dividir_csv_filtrado(
            entrada=Path(args.entrada),
            saida_1=Path(args.saida_1),
            saida_2=Path(args.saida_2),
            delimitador=args.delimitador,
        )
        print(
            f"Linhas filtradas: {total}. "
            f"Arquivo 1: {total_1} linhas. "
            f"Arquivo 2: {total_2} linhas."
        )
        return

    if args.comando == "comparar":
        resumo = comparar_chaves_csv(
            csv_base=Path(args.arquivo_1),
            csv_comparacao=Path(args.arquivo_2),
            saida=Path(args.saida),
            delimitador=args.delimitador,
            coluna_chave=args.coluna_chave,
        )
        print(
            f"Arquivo 1: {resumo['arquivo_1']} chaves. "
            f"Arquivo 2: {resumo['arquivo_2']} chaves. "
            f"Nos dois: {resumo['presentes_nos_dois']}. "
            f"Faltando no arquivo 1: {resumo['faltando_no_arquivo_1']}. "
            f"Faltando no arquivo 2: {resumo['faltando_no_arquivo_2']}."
        )
        return

    resumo = gerar_analise_faltantes_da_base(
        csv_base=Path(args.base),
        csv_conferido=Path(args.conferido),
        saida=Path(args.saida),
        delimitador=args.delimitador,
        coluna_chave=args.coluna_chave,
    )
    print(
        f"Base: {resumo['base']} chaves. "
        f"Conferido: {resumo['conferido']} chaves. "
        f"Faltando no conferido: {resumo['faltando_no_conferido']}."
    )


if __name__ == "__main__":
    main()
