import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from bot_visual import BotVisual
from config_ufs import obter_config_por_chave
from extrator_nfce import extrair_campos_nfce
from rotinas_estaduais_2 import criar_rotina


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


@dataclass
class ResultadoProcessamento:
    linha: dict
    campos_nfce: dict


def processar_csv(
    entrada: Path,
    saida: Path,
    delimitador: str,
    modo: str,
    repetir_sem_itens: bool = False,
    max_tentativas_sem_itens: int = 2,
):
    pasta_textos = saida.parent / "textos_capturados"
    pasta_textos.mkdir(parents=True, exist_ok=True)

    with entrada.open("r", encoding="utf-8-sig", newline="") as arquivo_entrada:
        leitor = csv.DictReader(arquivo_entrada, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError("O CSV precisa ter cabecalho.")

        primeira_coluna = leitor.fieldnames[0]
        fieldnames_saida = _montar_fieldnames_saida(leitor.fieldnames)

        bot = BotVisual()
        linhas_saida = []
        contexto = _criar_contexto_lote(bot=bot, modo=modo)

        for indice, linha_original in enumerate(leitor, start=2):
            resultado = _processar_linha_csv(
                linha_original=linha_original,
                indice=indice,
                primeira_coluna=primeira_coluna,
                pasta_textos=pasta_textos,
                contexto=contexto,
                repetir_sem_itens=repetir_sem_itens,
                max_tentativas_sem_itens=max_tentativas_sem_itens,
            )
            linhas_saida.extend(_expandir_resultado_saida(resultado))

    with saida.open("w", encoding="utf-8", newline="") as arquivo_saida:
        escritor = csv.DictWriter(arquivo_saida, fieldnames=fieldnames_saida, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows(_filtrar_campos_saida(linhas_saida, fieldnames_saida))


def _montar_fieldnames_saida(fieldnames_entrada: list[str]) -> list[str]:
    fieldnames_saida = list(fieldnames_entrada)
    for campo in CAMPOS_ADICIONAIS:
        if campo not in fieldnames_saida:
            fieldnames_saida.append(campo)
    return fieldnames_saida


def _criar_contexto_lote(bot: BotVisual, modo: str) -> dict:
    return {
        "bot": bot,
        "modo": modo,
        "config_arquivo": None,
        "rotina_arquivo": None,
        "erro_fatal_lote": None,
    }


def _processar_linha_csv(
    *,
    linha_original: dict,
    indice: int,
    primeira_coluna: str,
    pasta_textos: Path,
    contexto: dict,
    repetir_sem_itens: bool,
    max_tentativas_sem_itens: int,
) -> ResultadoProcessamento:
    linha = dict(linha_original)
    chave = (linha.get(primeira_coluna) or "").strip()

    if not chave:
        linha["status_robo"] = "erro"
        linha["observacao"] = f"Linha {indice} sem chave na primeira coluna."
        return ResultadoProcessamento(linha=linha, campos_nfce=extrair_campos_nfce(""))

    if contexto["erro_fatal_lote"]:
        linha["status_robo"] = "erro"
        linha["observacao"] = contexto["erro_fatal_lote"]
        return _finalizar_resultado_linha(
            linha=linha,
            chave=chave,
            pasta_textos=pasta_textos,
            campos_nfce=extrair_campos_nfce(linha.get("texto_capturado", "")),
        )

    resultado = _executar_consulta_com_retentativa(
        chave=chave,
        linha=linha,
        indice=indice,
        contexto=contexto,
        repetir_sem_itens=repetir_sem_itens,
        max_tentativas_sem_itens=max_tentativas_sem_itens,
    )

    return _finalizar_resultado_linha(
        linha=resultado.linha,
        chave=chave,
        pasta_textos=pasta_textos,
        campos_nfce=resultado.campos_nfce,
    )


def _executar_consulta_com_retentativa(
    *,
    chave: str,
    linha: dict,
    indice: int,
    contexto: dict,
    repetir_sem_itens: bool,
    max_tentativas_sem_itens: int,
) -> ResultadoProcessamento:
    tentativas = _calcular_total_tentativas(
        repetir_sem_itens=repetir_sem_itens,
        max_tentativas_sem_itens=max_tentativas_sem_itens,
    )
    melhor_resultado = None

    for tentativa in range(1, tentativas + 1):
        linha_tentativa = dict(linha)
        resultado = _executar_consulta_uma_vez(
            chave=chave,
            linha=linha_tentativa,
            indice=indice,
            contexto=contexto,
        )
        melhor_resultado = resultado

        if resultado.campos_nfce["tem_itens"] == "sim":
            if tentativa > 1:
                resultado.linha["observacao"] = _mesclar_observacoes(
                    resultado.linha.get("observacao", ""),
                    f"Itens encontrados apos retentativa {tentativa}/{tentativas}.",
                )
            return resultado

        if tentativa < tentativas and _deve_repetir_por_sem_itens(resultado):
            resultado.linha["observacao"] = _mesclar_observacoes(
                resultado.linha.get("observacao", ""),
                f"Sem itens apos tentativa {tentativa}/{tentativas}. Nova consulta sera executada.",
            )
            continue

        break

    return melhor_resultado or ResultadoProcessamento(linha=linha, campos_nfce=extrair_campos_nfce(""))


def _calcular_total_tentativas(*, repetir_sem_itens: bool, max_tentativas_sem_itens: int) -> int:
    tentativas_adicionais = max(0, max_tentativas_sem_itens)
    return 1 + tentativas_adicionais if repetir_sem_itens else 1


def _executar_consulta_uma_vez(*, chave: str, linha: dict, indice: int, contexto: dict) -> ResultadoProcessamento:
    try:
        config = obter_config_por_chave(chave)
        rotina = _obter_rotina_para_linha(
            config=config,
            indice=indice,
            contexto=contexto,
        )
        resultado_execucao = rotina.executar(chave, linha)
        linha.update(resultado_execucao)
    except Exception as erro:
        linha["status_robo"] = "erro"
        linha["observacao"] = str(erro)

        rotina_arquivo = contexto["rotina_arquivo"]
        config_arquivo = contexto["config_arquivo"]
        if rotina_arquivo is not None and not rotina_arquivo.pagina_inicializada and config_arquivo is not None:
            contexto["erro_fatal_lote"] = (
                f"Falha ao abrir ou confirmar a pagina inicial da UF {config_arquivo.uf}. "
                f"Erro original: {erro}"
            )

    campos_nfce = extrair_campos_nfce(linha.get("texto_capturado", ""))
    return ResultadoProcessamento(linha=linha, campos_nfce=campos_nfce)


def _obter_rotina_para_linha(*, config, indice: int, contexto: dict):
    config_arquivo = contexto["config_arquivo"]
    rotina_arquivo = contexto["rotina_arquivo"]

    if config_arquivo is None:
        contexto["config_arquivo"] = config
        contexto["rotina_arquivo"] = criar_rotina(contexto["bot"], config, contexto["modo"])
        return contexto["rotina_arquivo"]

    if config.codigo_ibge != config_arquivo.codigo_ibge:
        raise ValueError(
            f"CSV com mais de uma UF. Esperado estado {config_arquivo.uf}, "
            f"mas a linha {indice} veio com estado {config.uf}."
        )

    return rotina_arquivo


def _deve_repetir_por_sem_itens(resultado: ResultadoProcessamento) -> bool:
    if resultado.linha.get("status_robo") == "erro":
        return False
    return resultado.campos_nfce["tem_itens"] == "nao"


def _finalizar_resultado_linha(
    *,
    linha: dict,
    chave: str,
    pasta_textos: Path,
    campos_nfce: dict,
) -> ResultadoProcessamento:
    linha["arquivo_texto_capturado"] = _salvar_texto_capturado(
        pasta_textos=pasta_textos,
        chave=chave,
        texto=linha.get("texto_capturado", ""),
    )
    _aplicar_campos_nfce_na_linha(linha, campos_nfce)
    return ResultadoProcessamento(linha=linha, campos_nfce=campos_nfce)


def _aplicar_campos_nfce_na_linha(linha: dict, campos_nfce: dict):
    linha["nota_numero"] = campos_nfce["nota_numero"]
    linha["nota_emissao"] = campos_nfce["nota_emissao"]
    linha["tem_itens"] = campos_nfce["tem_itens"]
    linha["tem_combustivel"] = campos_nfce["tem_combustivel"]
    linha["combustiveis"] = campos_nfce["combustiveis"]
    linha["litros_total"] = campos_nfce["litros_total"]
    linha["valor_itens_combustivel"] = campos_nfce["valor_itens_combustivel"]


def _expandir_resultado_saida(resultado: ResultadoProcessamento) -> list[dict]:
    linha = resultado.linha
    itens = resultado.campos_nfce["itens"]

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


def _mesclar_observacoes(observacao_atual: str, complemento: str) -> str:
    observacao_atual = (observacao_atual or "").strip()
    complemento = complemento.strip()
    if not observacao_atual:
        return complemento
    if complemento in observacao_atual:
        return observacao_atual
    return f"{observacao_atual} {complemento}"


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
    parser.add_argument(
        "--repetir-sem-itens",
        action="store_true",
        help="Quando o scraping concluir sem itens, refaz a consulta apenas da chave atual.",
    )
    parser.add_argument(
        "--max-tentativas-sem-itens",
        type=int,
        default=2,
        help="Quantidade de retentativas extras para chaves que terminarem sem itens.",
    )
    return parser


if __name__ == "__main__":
    args = criar_parser().parse_args()
    processar_csv(
        entrada=Path(args.entrada),
        saida=Path(args.saida),
        delimitador=args.delimitador,
        modo=args.modo,
        repetir_sem_itens=args.repetir_sem_itens,
        max_tentativas_sem_itens=args.max_tentativas_sem_itens,
    )
