import logging

from robo_nfce.rotinas.base import RotinaEstado
from robo_nfce.rotinas.mg import classificacao as estados

logger = logging.getLogger(__name__)


class RotinaMGPadrao(RotinaEstado):
    """Consulta no portal de MG: valida cada etapa pelo texto copiado da pagina (Ctrl+A/Ctrl+C)."""

    URL_INICIAL = "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/consultaarg.xhtml"
    MAX_TENTATIVAS_CONSULTA = 5
    TENTATIVA_RECARREGAR = 3

    # Areas (x_min, x_max, y_min, y_max) calibradas para a tela atual.
    # O layout "erro" desloca campo e botao para baixo.
    AREA_CAMPO_CHAVE_INICIAL = (1651, 2365, 391, 408)
    AREA_CAMPO_CHAVE_ERRO = (1651, 2365, 429, 455)
    AREA_BOTAO_CONSULTAR_INICIAL = (1647, 1923, 503, 523)
    AREA_BOTAO_CONSULTAR_ERRO = (1647, 1923, 550, 576)
    PONTO_CLOUDFLARE = (285, 495)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._estado_pagina = estados.INICIAL

    # ---------- fluxo principal ----------

    def _preparar_pagina(self) -> None:
        if not self.pagina_inicializada:
            logger.info("Abrindo link da UF %s uma vez: %s", self.config.uf, self.URL_INICIAL)
        else:
            logger.info("Verificando pagina inicial da UF %s para a proxima chave", self.config.uf)

        self._estado_pagina = self._garantir_pagina_inicial()
        self.pagina_inicializada = True
        logger.info("MG pagina inicial pronta; iniciando fluxo da consulta")

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        estado = self._estado_pagina
        texto = ""
        estado_final = ""

        for tentativa in range(1, self.MAX_TENTATIVAS_CONSULTA + 1):
            if tentativa == self.TENTATIVA_RECARREGAR:
                self.bot.atualizar_pagina(self.URL_INICIAL, espera=6)

            logger.info("MG tentativa consulta -> %s (estado antes do clique: %s)", tentativa, estado)
            x_botao, y_botao = self._preparar_tentativa(estado, chave)
            self._clicar_botao_consultar(x_botao, y_botao)

            # Depois do clique, o texto real da pagina decide se veio resultado,
            # se continua em tela inicial/erro recuperavel ou caiu em estado desconhecido.
            texto = self._copiar_texto_pagina()
            estado_final = estados.classificar_estado_pagina(texto)

            if estado_final == estados.RESULTADO:
                logger.info("MG confirmou resultado pelo texto copiado")
                break

            if estados.estado_exige_reinicio(estado_final):
                logger.info("MG texto apos consultar fora dos estados esperados; reiniciando aba")
                self._reiniciar_aba_consulta()
                self._preencher_chave(chave, *self._ponto_campo_chave(estados.INICIAL))
                self.bot.esperar(2)
                texto = ""
                continue

            logger.info("MG ainda em tela inicial/erro recuperavel, tentando novamente")
        else:
            logger.info("MG nao confirmou pelo clipboard, caindo para OCR")
            texto = ""

        if not texto:
            texto, estado_final = self._capturar_por_ocr(estado_final)
        elif estado_final != estados.RESULTADO:
            texto = ""

        logger.info("MG finalizando execucao da chave atual")
        return self._resultado(
            texto_capturado=texto,
            observacao="Rotina MG validada pelo texto copiado contendo a tabela de 'Produtos e Servicos'.",
        )

    def _capturar_por_ocr(self, estado_final: str) -> tuple[str, str]:
        logger.info("MG executando OCR como ultimo recurso")
        texto_ocr = self.bot.extrair_texto_pagina("captura_mg")
        logger.info("MG OCR retornou -> %s caracteres", len(texto_ocr))
        estado_ocr = estados.classificar_estado_pagina(texto_ocr) if texto_ocr else ""
        if estado_ocr == estados.RESULTADO:
            logger.info("MG OCR confirmou resultado")
            return texto_ocr, estado_ocr
        logger.info("MG OCR nao confirmou resultado; descartando texto capturado")
        return "", estado_ocr or estado_final

    def _preparar_tentativa(self, estado: str, chave: str) -> tuple[int, int]:
        """Preenche a chave conforme o layout atual e retorna o ponto do botao consultar."""
        if estado == estados.INICIAL:
            self._preencher_chave(chave, *self._ponto_campo_chave(estado))
            return self._ponto_botao_consultar(estado)

        if estado == estados.ERRO:
            self._preencher_chave(chave, *self._ponto_campo_chave(estado))
            self._clicar_cloudflare()
            return self._ponto_botao_consultar(estado)

        # Estado fora do fluxo: tela corrompida, recria a pagina inicial.
        logger.info("MG estado fora do fluxo esperado antes do clique; reiniciando pagina inicial")
        self._reiniciar_aba_consulta()
        self._preencher_chave(chave, *self._ponto_campo_chave(estados.INICIAL))
        self.bot.esperar(2)
        return self._ponto_botao_consultar(estados.INICIAL)

    # ---------- pagina inicial ----------

    def _garantir_pagina_inicial(self, espera: int = 8, max_tentativas: int = 4, forcar_recarga: bool = False) -> str:
        self.bot.atualizar_pagina(self.URL_INICIAL, espera=4)
        for tentativa in range(1, max_tentativas + 1):
            logger.info("MG garantindo pagina inicial -> tentativa %s/%s", tentativa, max_tentativas)
            url_atual = self.bot.obter_url_atual()
            url_ja_inicial = estados.normalizar_url(url_atual) == estados.normalizar_url(self.URL_INICIAL)

            if not (not forcar_recarga and tentativa == 1 and url_ja_inicial):
                logger.info("MG reenviando URL inicial e recarregando")
                self.bot.abrir_site(self.URL_INICIAL, espera=espera)
                self.bot.atualizar_pagina(self.URL_INICIAL, espera=espera)

            estado_atual = estados.classificar_estado_pagina(self._copiar_texto_pagina())
            if estado_atual == estados.INICIAL:
                logger.info("MG confirmou a tela inicial correta")
                return estado_atual

        raise TimeoutError("MG nao confirmou a tela inicial correta apos varias tentativas de recarga.")

    def _reiniciar_aba_consulta(self) -> None:
        logger.info("MG reiniciando fluxo pela URL inicial")
        self._garantir_pagina_inicial(espera=3, max_tentativas=4, forcar_recarga=True)
        self.pagina_inicializada = True

    # ---------- interacao com a tela ----------

    def _copiar_texto_pagina(self) -> str:
        self.bot.focar_pagina()
        texto = self.bot.selecionar_tudo_e_copiar().strip()
        logger.info("MG texto copiado -> %s caracteres", len(texto))
        logger.debug("MG texto copiado:\n%s", texto)
        return texto

    def _preencher_chave(self, chave: str, x_campo: int, y_campo: int) -> None:
        logger.info("MG preenchendo chave no campo -> x=%s, y=%s", x_campo, y_campo)
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.clicar(x_campo, y_campo)
        self.bot.atalho("ctrl", "a")
        self.bot.colar_texto(chave)

    def _clicar_botao_consultar(self, x_botao: int, y_botao: int) -> None:
        logger.info("MG clicando botao consultar -> x=%s, y=%s", x_botao, y_botao)
        self.bot.mover_mouse_humano(x_botao, y_botao)
        self.bot.esperar(0.2)
        self.bot.clicar(x_botao, y_botao)
        self.bot.esperar(4)

    def _clicar_cloudflare(self) -> None:
        self.bot.mover_mouse_humano(*self.PONTO_CLOUDFLARE)
        self.bot.esperar(0.2)
        self.bot.clicar(*self.PONTO_CLOUDFLARE)
        self.bot.esperar(0.5)

    def _ponto_campo_chave(self, estado: str) -> tuple[int, int]:
        area = self.AREA_CAMPO_CHAVE_ERRO if estado == estados.ERRO else self.AREA_CAMPO_CHAVE_INICIAL
        return self.bot.ponto_aleatorio(*area)

    def _ponto_botao_consultar(self, estado: str) -> tuple[int, int]:
        area = self.AREA_BOTAO_CONSULTAR_ERRO if estado == estados.ERRO else self.AREA_BOTAO_CONSULTAR_INICIAL
        return self.bot.ponto_aleatorio(*area)
