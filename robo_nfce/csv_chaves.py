"""Ferramentas para dividir CSVs e comparar chaves entre arquivos."""

from pathlib import Path

from robo_nfce.utils.csv_io import escrever_csv, ler_csv


def filtrar_linhas_sem_itens_e_sem_combustivel(linhas: list[dict]) -> list[dict]:
    return [
        linha for linha in linhas
        if (linha.get("tem_itens") or "").strip().lower() == "nao"
        and (linha.get("tem_combustivel") or "").strip().lower() == "nao"
    ]


def dividir_lista_ao_meio(linhas: list[dict]) -> tuple[list[dict], list[dict]]:
    """A primeira metade fica com a linha extra quando o total e impar."""
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
    return {chave for linha in linhas if (chave := (linha.get(coluna_chave) or "").strip())}


def comparar_chaves_csv(
    csv_base: Path,
    csv_comparacao: Path,
    saida: Path,
    delimitador: str = ",",
    coluna_chave: str = "chave",
) -> dict[str, int]:
    _, linhas_base = ler_csv(csv_base, delimitador)
    _, linhas_comparacao = ler_csv(csv_comparacao, delimitador)

    chaves_1 = coletar_chaves(linhas_base, coluna_chave)
    chaves_2 = coletar_chaves(linhas_comparacao, coluna_chave)

    linhas_saida = []
    contagem = {"presente_nos_dois": 0, "faltando_no_arquivo_1": 0, "faltando_no_arquivo_2": 0}

    for chave in sorted(chaves_1 | chaves_2):
        no_1 = chave in chaves_1
        no_2 = chave in chaves_2
        if no_1 and no_2:
            status = "presente_nos_dois"
        elif no_1:
            status = "faltando_no_arquivo_2"
        else:
            status = "faltando_no_arquivo_1"
        contagem[status] += 1

        linhas_saida.append({
            coluna_chave: chave,
            "status_comparacao": status,
            "presente_arquivo_1": "sim" if no_1 else "nao",
            "presente_arquivo_2": "sim" if no_2 else "nao",
        })

    escrever_csv(
        saida,
        [coluna_chave, "status_comparacao", "presente_arquivo_1", "presente_arquivo_2"],
        linhas_saida,
        delimitador,
    )

    return {
        "arquivo_1": len(chaves_1),
        "arquivo_2": len(chaves_2),
        "presentes_nos_dois": contagem["presente_nos_dois"],
        "faltando_no_arquivo_1": contagem["faltando_no_arquivo_1"],
        "faltando_no_arquivo_2": contagem["faltando_no_arquivo_2"],
    }


def gerar_analise_faltantes_da_base(
    csv_base: Path,
    csv_conferido: Path,
    saida: Path,
    delimitador: str = ",",
    coluna_chave: str = "chave",
) -> dict[str, int]:
    """Grava as linhas da base (1 por chave, cabecalho original) cuja chave nao esta no conferido."""
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
        if chave not in chaves_conferido:
            linhas_saida.append(dict(linha))

    escrever_csv(saida, fieldnames_base, linhas_saida, delimitador)

    return {
        "base": len(chaves_vistas),
        "conferido": len(chaves_conferido),
        "faltando_no_conferido": len(linhas_saida),
    }
