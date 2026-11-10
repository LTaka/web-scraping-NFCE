"""Classifica o texto copiado do portal NFC-e de MG (sem dependencia de interface grafica)."""

import logging

from robo_nfce.utils.texto import normalizar_espacos

logger = logging.getLogger(__name__)

RESULTADO = "resultado"
ERRO = "erro"
INICIAL = "inicial"
DESCONHECIDO = "desconhecido"

ESTADOS_RECUPERAVEIS = {INICIAL, ERRO}

TEXTO_SUCESSO = "Produtos e Serviços"
TEXTO_RESULTADO = "Consulta Resumida - Ambiente de Produção"

FRAGMENTOS_PAGINA_INICIAL = (
    "Consultar NFC-e",
    "Consultar Inutilização",
    "Nota Fiscal de Consumidor Eletrônica (NFC-e) - Ambiente de Produção",
    "Observações",
    "1. Chave de Acesso deve ser informado o número de 44 dígitos NFC-e (Nota Fiscal de Consumidor Eletrônica)",
    "2. reCAPTCHA é um serviço que protege este site contra spam e abuso, passe por ele para prosseguir com a solicitação de consulta.",
    "Consulta Nota Fiscal de Consumidor Eletrônica (NFC-e)",
    "Chave de acesso",
    "Versão 1.2.27",
    "Rodovia Papa João Paulo II, 4.001 - Prédio Gerais (6º e 7º andares) - Bairro Serra Verde, Belo Horizonte/MG CEP 31630-901",
)

# Texto alem dos fragmentos fixos da pagina inicial. Acima deste limite,
# considera que ha mensagem de erro deslocando o layout.
LIMITE_EXCEDENTE_PAGINA_INICIAL = 120


def tem_fragmentos_pagina_inicial(texto: str) -> bool:
    texto_normalizado = normalizar_espacos(texto)
    return all(fragmento.lower() in texto_normalizado for fragmento in FRAGMENTOS_PAGINA_INICIAL)


def texto_excedente(texto: str) -> str:
    excedente = normalizar_espacos(texto)
    for fragmento in FRAGMENTOS_PAGINA_INICIAL:
        excedente = excedente.replace(fragmento.lower(), " ")
    return " ".join(excedente.split())


def eh_resultado(texto: str) -> bool:
    texto_normalizado = (texto or "").lower()
    return TEXTO_RESULTADO.lower() in texto_normalizado or TEXTO_SUCESSO.lower() in texto_normalizado


def eh_pagina_erro(texto: str) -> bool:
    if not tem_fragmentos_pagina_inicial(texto):
        return False
    excedente = texto_excedente(texto)
    logger.debug("MG excedente para layout de erro -> %s caracteres: %s", len(excedente), excedente)
    return len(excedente) > LIMITE_EXCEDENTE_PAGINA_INICIAL


def eh_pagina_inicial(texto: str) -> bool:
    if not tem_fragmentos_pagina_inicial(texto):
        return False
    return len(texto_excedente(texto)) <= LIMITE_EXCEDENTE_PAGINA_INICIAL


def classificar_estado_pagina(texto: str) -> str:
    if eh_resultado(texto):
        estado = RESULTADO
    elif eh_pagina_erro(texto):
        estado = ERRO
    elif eh_pagina_inicial(texto):
        estado = INICIAL
    else:
        estado = DESCONHECIDO
    logger.info("MG classificacao de estado -> %s (%s caracteres)", estado, len(texto or ""))
    return estado


def estado_exige_reinicio(estado: str) -> bool:
    return estado not in ESTADOS_RECUPERAVEIS and estado != RESULTADO


def normalizar_url(url: str) -> str:
    return (url or "").strip().rstrip("/").lower()
