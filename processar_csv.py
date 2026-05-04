import argparse
import csv
from pathlib import Path

from bot_visual import BotVisual
from config_ufs import obter_config_por_chave
from extrator_nfce import extrair_campos_nfce
from rotinas_estaduais import criar_rotina


CAMPOS_ADICIONAIS = [
    "uf",
    "url_consulta",
    "status_robo",
    "arquivo_texto_capturado",
    "observacao",
    "nota_numero",
    "nota_emissao",
    "item_descricao",
    "item_qtde",
    "item_un",
    "item_vl_unit",
    "item_vl_total",
]


def processar_csv(entrada: Path, saida: Path, delimitador: str, modo: str):
    pasta_textos = saida.parent / "textos_capturados"
    pasta_textos.mkdir(parents=True, exist_ok=True)

    with entrada.open("r", encoding="utf-8-sig", newline="") as arquivo_entrada:
        leitor = csv.DictReader(arquivo_entrada, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError("O CSV precisa ter cabecalho.")

        primeira_coluna = leitor.fieldnames[0]
        fieldnames_saida = list(leitor.fieldnames)
        for campo in CAMPOS_ADICIONAIS:
            if campo not in fieldnames_saida:
                fieldnames_saida.append(campo)

        bot = BotVisual()
        linhas_saida = []
        config_arquivo = None
        rotina_arquivo = None
        erro_fatal_lote = None

        for indice, linha in enumerate(leitor, start=2):
            chave = (linha.get(primeira_coluna) or "").strip()
            if not chave:
                linha["status_robo"] = "erro"
                linha["observacao"] = f"Linha {indice} sem chave na primeira coluna."
                linhas_saida.append(linha)
                continue

            if erro_fatal_lote:
                linha["status_robo"] = "erro"
                linha["observacao"] = erro_fatal_lote
                linhas_saida.extend(_expandir_linhas_saida(linha))
                continue

            try:
                config = obter_config_por_chave(chave)

                if config_arquivo is None:
                    config_arquivo = config
                    rotina_arquivo = criar_rotina(bot, config_arquivo, modo)
                elif config.codigo_ibge != config_arquivo.codigo_ibge:
                    raise ValueError(
                        f"CSV com mais de uma UF. Esperado estado {config_arquivo.uf}, "
                        f"mas a linha {indice} veio com estado {config.uf}."
                    )

                resultado = rotina_arquivo.executar(chave, linha)
                linha.update(resultado)
            except Exception as erro:
                linha["status_robo"] = "erro"
                linha["observacao"] = str(erro)
                if rotina_arquivo is not None and not rotina_arquivo.pagina_inicializada:
                    erro_fatal_lote = (
                        f"Falha ao abrir ou confirmar a pagina inicial da UF {config_arquivo.uf}. "
                        f"Erro original: {erro}"
                    )

            linha["arquivo_texto_capturado"] = _salvar_texto_capturado(
                pasta_textos=pasta_textos,
                chave=chave,
                texto=linha.get("texto_capturado", ""),
            )
            linhas_saida.extend(_expandir_linhas_saida(linha))

    with saida.open("w", encoding="utf-8", newline="") as arquivo_saida:
        escritor = csv.DictWriter(arquivo_saida, fieldnames=fieldnames_saida, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows(_filtrar_campos_saida(linhas_saida, fieldnames_saida))


def _expandir_linhas_saida(linha: dict) -> list[dict]:
    campos_nfce = extrair_campos_nfce(linha.get("texto_capturado", ""))
    itens = campos_nfce["itens"]

    linha["nota_numero"] = campos_nfce["nota_numero"]
    linha["nota_emissao"] = campos_nfce["nota_emissao"]
    linha["tem_itens"] = campos_nfce["tem_itens"]
    linha["tem_combustivel"] = campos_nfce["tem_combustivel"]
    linha["combustiveis"] = campos_nfce["combustiveis"]
    linha["litros_total"] = campos_nfce["litros_total"]
    linha["valor_itens_combustivel"] = campos_nfce["valor_itens_combustivel"]

    if not itens:
        linha_sem_item = dict(linha)
        linha_sem_item["item_descricao"] = ""
        linha_sem_item["item_qtde"] = ""
        linha_sem_item["item_un"] = ""
        linha_sem_item["item_vl_unit"] = ""
        linha_sem_item["item_vl_total"] = ""
        return [linha_sem_item]

    linhas_expandidas = []

    for item in itens:
        linha_item = dict(linha)
        linha_item["item_descricao"] = item["item_descricao"]
        linha_item["item_qtde"] = item["item_qtde"]
        linha_item["item_un"] = item["item_un"]
        linha_item["item_vl_unit"] = item["item_vl_unit"]
        linha_item["item_vl_total"] = item["item_vl_total"]
        linhas_expandidas.append(linha_item)

    return linhas_expandidas

def _salvar_texto_capturado(pasta_textos: Path, chave: str, texto: str) -> str:
    if not texto or not texto.strip():
        return ""

    caminho = pasta_textos / f"{chave}.txt"
    caminho.write_text(texto, encoding="utf-8")
    return str(caminho)


def _filtrar_campos_saida(linhas: list[dict], fieldnames_saida: list[str]) -> list[dict]:
    campos_permitidos = set(fieldnames_saida)
    return [{campo: linha.get(campo, "") for campo in fieldnames_saida if campo in campos_permitidos} for linha in linhas]


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Processa um CSV e chama a rotina correta com base nos 2 primeiros digitos da chave.",
    )
    parser.add_argument("entrada", help="Caminho do CSV de entrada.")
    parser.add_argument(
        "--saida",
        default="saida_enriquecida.csv",
        help="Caminho do CSV de saida.",
    )
    parser.add_argument(
        "--delimitador",
        default=",",
        help="Delimitador do CSV. Exemplo: ',' ou ';'.",
    )
    parser.add_argument(
        "--modo",
        choices=["simular", "executar"],
        default="simular",
        help="Use 'executar' para rodar o bot visual de verdade.",
    )
    return parser


if __name__ == "__main__":
    args = criar_parser().parse_args()
    processar_csv(
        entrada=Path(args.entrada),
        saida=Path(args.saida),
        delimitador=args.delimitador,
        modo=args.modo,
    )
