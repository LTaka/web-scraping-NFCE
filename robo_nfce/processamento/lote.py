"""Le o CSV base, consulta cada chave na rotina da UF e grava o CSV enriquecido."""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from robo_nfce.config import ConfigUF, obter_config_por_chave
from robo_nfce.extracao.linhas import CAMPOS_ITEM, aplicar_campos_nfce, expandir_por_itens
from robo_nfce.extracao.nfce import extrair_campos_nfce
from robo_nfce.rotinas import criar_rotina
from robo_nfce.rotinas.base import MODO_EXECUTAR, RotinaEstado
from robo_nfce.utils.csv_io import adicionar_colunas, escrever_csv
from robo_nfce.utils.texto import mesclar_observacoes

logger = logging.getLogger(__name__)

ESPERA_PREPARACAO_INICIAL = 5
PASTA_TEXTOS_CAPTURADOS = "textos_capturados"

CAMPOS_ADICIONAIS = [
    "uf",
    "arquivo_texto_capturado",
    "nota_numero",
    "nota_emissao",
    *CAMPOS_ITEM,
]


@dataclass
class ResultadoProcessamento:
    linha: dict
    campos_nfce: dict


@dataclass
class ContextoLote:
    """Estado compartilhado entre as linhas: o CSV inteiro deve ser de uma unica UF."""

    bot: Any
    modo: str
    config: ConfigUF | None = None
    rotina: RotinaEstado | None = None
    erro_fatal: str | None = None


def processar_csv(
    entrada: Path,
    saida: Path,
    delimitador: str = ",",
    modo: str = "simular",
    repetir_sem_itens: bool = False,
    max_tentativas_sem_itens: int = 2,
    somente_sem_itens: bool = False,
) -> int:
    """Processa o CSV e retorna a quantidade de chaves consultadas."""
    from robo_nfce.bot.visual import BotVisual  # importa pyautogui apenas quando necessario

    pasta_textos = saida.parent / PASTA_TEXTOS_CAPTURADOS
    pasta_textos.mkdir(parents=True, exist_ok=True)

    with entrada.open("r", encoding="utf-8-sig", newline="") as arquivo_entrada:
        leitor = csv.DictReader(arquivo_entrada, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError("O CSV precisa ter cabecalho.")
        coluna_chave = leitor.fieldnames[0]
        fieldnames_saida = montar_fieldnames_saida(leitor.fieldnames)
        linhas_entrada = carregar_linhas_entrada(
            leitor=leitor,
            coluna_chave=coluna_chave,
            somente_sem_itens=somente_sem_itens,
        )

    bot = BotVisual()
    _aguardar_preparacao_inicial(bot, modo)
    contexto = ContextoLote(bot=bot, modo=modo)

    linhas_saida = []
    for indice, linha_original in linhas_entrada:
        resultado = processar_linha(
            linha_original=linha_original,
            indice=indice,
            coluna_chave=coluna_chave,
            pasta_textos=pasta_textos,
            contexto=contexto,
            repetir_sem_itens=repetir_sem_itens,
            max_tentativas_sem_itens=max_tentativas_sem_itens,
        )
        linhas_saida.extend(expandir_por_itens(resultado.linha, resultado.campos_nfce["itens"]))

    escrever_csv(saida, fieldnames_saida, linhas_saida, delimitador)
    return len(linhas_entrada)


def montar_fieldnames_saida(fieldnames_entrada: list[str]) -> list[str]:
    return adicionar_colunas(fieldnames_entrada, CAMPOS_ADICIONAIS)


def carregar_linhas_entrada(
    *, leitor: csv.DictReader, coluna_chave: str, somente_sem_itens: bool
) -> list[tuple[int, dict]]:
    """Retorna (numero_da_linha_no_arquivo, linha). Com `somente_sem_itens`, filtra e deduplica por chave."""
    linhas = []
    chaves_vistas = set()

    for indice, linha in enumerate(leitor, start=2):
        if somente_sem_itens:
            if (linha.get("tem_itens") or "").strip().lower() != "nao":
                continue
            chave = (linha.get(coluna_chave) or "").strip()
            if chave:
                if chave in chaves_vistas:
                    continue
                chaves_vistas.add(chave)
        linhas.append((indice, linha))

    return linhas


def _aguardar_preparacao_inicial(bot, modo: str) -> None:
    if modo != MODO_EXECUTAR:
        return
    logger.info(
        "Aguardando %s segundos antes de iniciar o processamento. Posicione a pagina correta.",
        ESPERA_PREPARACAO_INICIAL,
    )
    bot.esperar(ESPERA_PREPARACAO_INICIAL)


def processar_linha(
    *,
    linha_original: dict,
    indice: int,
    coluna_chave: str,
    pasta_textos: Path,
    contexto: ContextoLote,
    repetir_sem_itens: bool,
    max_tentativas_sem_itens: int,
) -> ResultadoProcessamento:
    linha = dict(linha_original)
    chave = (linha.get(coluna_chave) or "").strip()

    if not chave:
        linha["status_robo"] = "erro"
        linha["observacao"] = f"Linha {indice} sem chave na primeira coluna."
        return ResultadoProcessamento(linha=linha, campos_nfce=extrair_campos_nfce(""))

    if contexto.erro_fatal:
        linha["status_robo"] = "erro"
        linha["observacao"] = contexto.erro_fatal
        resultado = ResultadoProcessamento(linha, extrair_campos_nfce(linha.get("texto_capturado", "")))
    else:
        logger.info("Linha %s: consultando chave %s", indice, chave)
        resultado = executar_consulta_com_retentativa(
            chave=chave,
            linha=linha,
            indice=indice,
            contexto=contexto,
            repetir_sem_itens=repetir_sem_itens,
            max_tentativas_sem_itens=max_tentativas_sem_itens,
        )

    resultado.linha["arquivo_texto_capturado"] = salvar_texto_capturado(
        pasta_textos, chave, resultado.linha.get("texto_capturado", "")
    )
    aplicar_campos_nfce(resultado.linha, resultado.campos_nfce)
    return resultado


def executar_consulta_com_retentativa(
    *,
    chave: str,
    linha: dict,
    indice: int,
    contexto: ContextoLote,
    repetir_sem_itens: bool,
    max_tentativas_sem_itens: int,
) -> ResultadoProcessamento:
    """Consulta a chave; com `repetir_sem_itens`, refaz enquanto vier sem itens (sem erro)."""
    tentativas = 1 + max(0, max_tentativas_sem_itens) if repetir_sem_itens else 1
    resultado = None

    for tentativa in range(1, tentativas + 1):
        resultado = executar_consulta_uma_vez(chave=chave, linha=dict(linha), indice=indice, contexto=contexto)

        if resultado.campos_nfce["tem_itens"] == "sim":
            if tentativa > 1:
                resultado.linha["observacao"] = mesclar_observacoes(
                    resultado.linha.get("observacao", ""),
                    f"Itens encontrados apos retentativa {tentativa}/{tentativas}.",
                )
            return resultado

        if tentativa < tentativas and _deve_repetir_por_sem_itens(resultado):
            resultado.linha["observacao"] = mesclar_observacoes(
                resultado.linha.get("observacao", ""),
                f"Sem itens apos tentativa {tentativa}/{tentativas}. Nova consulta sera executada.",
            )
            continue
        break

    return resultado or ResultadoProcessamento(linha=linha, campos_nfce=extrair_campos_nfce(""))


def executar_consulta_uma_vez(*, chave: str, linha: dict, indice: int, contexto: ContextoLote) -> ResultadoProcessamento:
    try:
        config = obter_config_por_chave(chave)
        rotina = _obter_rotina(config=config, indice=indice, contexto=contexto)
        linha.update(rotina.executar(chave, linha))
    except Exception as erro:  # noqa: BLE001 - qualquer falha vira status de erro na linha
        logger.exception("Erro ao consultar chave %s", chave)
        linha["status_robo"] = "erro"
        linha["observacao"] = str(erro)

        # Se nem a pagina inicial abriu, as proximas chaves falhariam igual: aborta o lote.
        if contexto.rotina is not None and not contexto.rotina.pagina_inicializada and contexto.config is not None:
            contexto.erro_fatal = (
                f"Falha ao abrir ou confirmar a pagina inicial da UF {contexto.config.uf}. "
                f"Erro original: {erro}"
            )

    return ResultadoProcessamento(linha=linha, campos_nfce=extrair_campos_nfce(linha.get("texto_capturado", "")))


def _obter_rotina(*, config: ConfigUF, indice: int, contexto: ContextoLote) -> RotinaEstado:
    if contexto.config is None:
        contexto.config = config
        contexto.rotina = criar_rotina(contexto.bot, config, contexto.modo)
        return contexto.rotina

    if config.codigo_ibge != contexto.config.codigo_ibge:
        raise ValueError(
            f"CSV com mais de uma UF. Esperado estado {contexto.config.uf}, "
            f"mas a linha {indice} veio com estado {config.uf}."
        )
    return contexto.rotina


def _deve_repetir_por_sem_itens(resultado: ResultadoProcessamento) -> bool:
    if resultado.linha.get("status_robo") == "erro":
        return False
    return resultado.campos_nfce["tem_itens"] == "nao"


def salvar_texto_capturado(pasta_textos: Path, chave: str, texto: str) -> str:
    if not texto or not texto.strip():
        return ""
    caminho = pasta_textos / f"{chave}.txt"
    caminho.write_text(texto, encoding="utf-8")
    return str(caminho)
