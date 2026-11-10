"""Linha de comando unica: `python -m robo_nfce <comando> ...`."""

import argparse
import logging
from pathlib import Path


def _caminho_opcional(valor: str | None) -> Path | None:
    return Path(valor) if valor else None


# ---------- processar ----------

def _registrar_processar(subparsers) -> None:
    parser = subparsers.add_parser(
        "processar",
        help="Consulta cada chave do CSV no portal da UF (2 primeiros digitos da chave).",
    )
    parser.add_argument("entrada", help="CSV de entrada (chave na primeira coluna).")
    parser.add_argument("--saida", default="saida_enriquecida.csv", help="CSV de saida.")
    parser.add_argument("--delimitador", default=",", help="Delimitador do CSV. Ex.: ',' ou ';'.")
    parser.add_argument(
        "--modo",
        choices=["simular", "executar"],
        default="simular",
        help="Use 'executar' para rodar o bot visual de verdade.",
    )
    parser.add_argument(
        "--repetir-sem-itens",
        action="store_true",
        help="Quando a consulta concluir sem itens, refaz apenas a chave atual.",
    )
    parser.add_argument(
        "--max-tentativas-sem-itens",
        type=int,
        default=2,
        help="Retentativas extras para chaves que terminarem sem itens.",
    )
    parser.add_argument(
        "--somente-sem-itens",
        action="store_true",
        help="Lendo um CSV ja processado, executa somente as linhas com tem_itens=nao.",
    )
    parser.set_defaults(executar=_cmd_processar)


def _cmd_processar(args) -> None:
    from robo_nfce.processamento.lote import processar_csv

    total = processar_csv(
        entrada=Path(args.entrada),
        saida=Path(args.saida),
        delimitador=args.delimitador,
        modo=args.modo,
        repetir_sem_itens=args.repetir_sem_itens,
        max_tentativas_sem_itens=args.max_tentativas_sem_itens,
        somente_sem_itens=args.somente_sem_itens,
    )
    logging.info("CSV processado com %s linha(s): %s", total, args.saida)


# ---------- extrair ----------

def _registrar_extrair(subparsers) -> None:
    parser = subparsers.add_parser(
        "extrair",
        help="Le textos capturados (.txt/.zip/pasta) e gera ou atualiza um CSV.",
    )
    parser.add_argument("entrada", help="Pasta com .txt, arquivo .txt ou arquivo .zip.")
    parser.add_argument("--saida", default="resultado.csv", help="CSV de saida.")
    parser.add_argument("--csv-base", default=None, help="CSV existente para atualizar pelas chaves.")
    parser.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    parser.add_argument(
        "--pasta-txt-filtrados",
        default=None,
        help="Pasta temporaria usada para extrair .txt quando a entrada for .zip.",
    )
    parser.add_argument(
        "--somente-sem-itens",
        action="store_true",
        help="Com --csv-base, atualiza apenas linhas com tem_itens=nao.",
    )
    parser.set_defaults(executar=_cmd_extrair)


def _cmd_extrair(args) -> None:
    from robo_nfce.extracao.textos_capturados import (
        atualizar_csv_existente_com_textos,
        gerar_csv_de_textos_capturados,
    )
    from robo_nfce.utils.arquivos import limpar_txt_filtrados, preparar_entrada_txt

    entrada_original = Path(args.entrada)
    entrada, _ = preparar_entrada_txt(entrada_original, _caminho_opcional(args.pasta_txt_filtrados))
    try:
        if args.csv_base:
            quantidade = atualizar_csv_existente_com_textos(
                entrada_csv=Path(args.csv_base),
                saida=Path(args.saida),
                pasta_textos=entrada,
                delimitador=args.delimitador,
                somente_sem_itens=args.somente_sem_itens,
            )
            logging.info("CSV atualizado com %s chave(s): %s", quantidade, args.saida)
        else:
            quantidade = gerar_csv_de_textos_capturados(entrada, Path(args.saida), args.delimitador)
            logging.info("CSV gerado com %s texto(s): %s", quantidade, args.saida)
    finally:
        if entrada_original.suffix.lower() == ".zip":
            limpar_txt_filtrados(entrada)


# ---------- sped ----------

def _registrar_sped(subparsers) -> None:
    parser = subparsers.add_parser(
        "sped",
        help="Converte SPED EFD (.txt, .zip ou pasta) no CSV base (C100 modelo 65).",
    )
    parser.add_argument("entrada", help="Arquivo .txt, .zip ou pasta com arquivos SPED.")
    parser.add_argument("--saida", default="exemplo_entrada.csv", help="CSV de saida.")
    parser.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    parser.add_argument(
        "--pasta-txt-filtrados",
        default=None,
        help="Pasta temporaria para os .txt selecionados quando a entrada for .zip.",
    )
    parser.set_defaults(executar=_cmd_sped)


def _cmd_sped(args) -> None:
    from robo_nfce.sped.arquivos import gerar_csv_base_do_sped

    total = gerar_csv_base_do_sped(
        entrada=args.entrada,
        saida=Path(args.saida),
        delimitador=args.delimitador,
        pasta_txt_filtrados=_caminho_opcional(args.pasta_txt_filtrados),
    )
    logging.info("CSV gerado com %s nota(s): %s", total, args.saida)


# ---------- csv (dividir / comparar / analisar-faltantes) ----------

def _registrar_csv(subparsers) -> None:
    parser = subparsers.add_parser("csv", help="Divide CSVs e compara chaves entre arquivos.")
    sub = parser.add_subparsers(dest="acao_csv", required=True)

    dividir = sub.add_parser(
        "dividir",
        help="Filtra tem_itens=nao e tem_combustivel=nao e divide em dois arquivos.",
    )
    dividir.add_argument("entrada", help="CSV de entrada.")
    dividir.add_argument("--saida-1", default="entrada_1.csv", help="Primeiro CSV de saida.")
    dividir.add_argument("--saida-2", default="entrada_2.csv", help="Segundo CSV de saida.")
    dividir.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    dividir.set_defaults(executar=_cmd_csv_dividir)

    comparar = sub.add_parser("comparar", help="Compara as chaves entre dois CSVs.")
    comparar.add_argument("arquivo_1", help="Primeiro CSV.")
    comparar.add_argument("arquivo_2", help="Segundo CSV.")
    comparar.add_argument("--saida", default="comparacao_chaves.csv", help="CSV de comparacao.")
    comparar.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    comparar.add_argument("--coluna-chave", default="chave", help="Coluna usada como chave.")
    comparar.set_defaults(executar=_cmd_csv_comparar)

    analisar = sub.add_parser(
        "analisar-faltantes",
        help="Gera CSV com as linhas da base que nao existem no conferido.",
    )
    analisar.add_argument("base", help="CSV principal, usado como base.")
    analisar.add_argument("conferido", help="CSV usado para conferencia.")
    analisar.add_argument("--saida", default="analise_faltantes.csv", help="CSV de analise.")
    analisar.add_argument("--delimitador", default=",", help="Delimitador do CSV.")
    analisar.add_argument("--coluna-chave", default="chave", help="Coluna usada como chave.")
    analisar.set_defaults(executar=_cmd_csv_analisar)


def _cmd_csv_dividir(args) -> None:
    from robo_nfce.csv_chaves import dividir_csv_filtrado

    total, total_1, total_2 = dividir_csv_filtrado(
        Path(args.entrada), Path(args.saida_1), Path(args.saida_2), args.delimitador
    )
    logging.info("Linhas filtradas: %s. Arquivo 1: %s linhas. Arquivo 2: %s linhas.", total, total_1, total_2)


def _cmd_csv_comparar(args) -> None:
    from robo_nfce.csv_chaves import comparar_chaves_csv

    resumo = comparar_chaves_csv(
        Path(args.arquivo_1), Path(args.arquivo_2), Path(args.saida), args.delimitador, args.coluna_chave
    )
    logging.info(
        "Arquivo 1: %s chaves. Arquivo 2: %s chaves. Nos dois: %s. "
        "Faltando no arquivo 1: %s. Faltando no arquivo 2: %s.",
        resumo["arquivo_1"],
        resumo["arquivo_2"],
        resumo["presentes_nos_dois"],
        resumo["faltando_no_arquivo_1"],
        resumo["faltando_no_arquivo_2"],
    )


def _cmd_csv_analisar(args) -> None:
    from robo_nfce.csv_chaves import gerar_analise_faltantes_da_base

    resumo = gerar_analise_faltantes_da_base(
        Path(args.base), Path(args.conferido), Path(args.saida), args.delimitador, args.coluna_chave
    )
    logging.info(
        "Base: %s chaves. Conferido: %s chaves. Faltando no conferido: %s.",
        resumo["base"],
        resumo["conferido"],
        resumo["faltando_no_conferido"],
    )


# ---------- entrada ----------

def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="robo_nfce",
        description="Robo de consulta de NFC-e por UF, extracao de textos e leitura de SPED.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Mostra logs detalhados (DEBUG).")
    subparsers = parser.add_subparsers(dest="comando", required=True)
    _registrar_processar(subparsers)
    _registrar_extrair(subparsers)
    _registrar_sped(subparsers)
    _registrar_csv(subparsers)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = criar_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    args.executar(args)


if __name__ == "__main__":
    main()
