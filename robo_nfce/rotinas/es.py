import logging

from robo_nfce.rotinas.base import RotinaEstado

logger = logging.getLogger(__name__)


class RotinaESPadrao(RotinaEstado):
    """Consulta no portal do ES: sucesso = URL mudar para a pagina do DANFE."""

    URL_RESULTADO = "https://app.sefaz.es.gov.br/ConsultaNFCe/ConsultaDANFE_NFCe.aspx"
    MAX_TENTATIVAS = 5

    # Coordenadas para o monitor principal. Valores do monitor 27" ficam nos comentarios.
    AREA_CAMPO_CHAVE = (172, 840, 339, 390)            # 27": (1672, 2419, 349, 418)
    AREA_BOTAO_PRIMEIRA_TENTATIVA = (174, 266, 407, 442)  # 27": (1674, 1778, 442, 479)
    AREA_BOTAO_DEMAIS_TENTATIVAS = (174, 266, 475, 505)   # 27": (1674, 1778, 523, 550)
    PONTO_ANTES_BOTAO = (890, 419)                     # 27": (2473, 452)

    def _preparar_pagina(self) -> None:
        if not self.pagina_inicializada:
            logger.info("Abrindo link da UF %s uma vez: %s", self.config.uf, self.config.url)
            self.bot.abrir_site(self.config.url)
            self.pagina_inicializada = True
        else:
            logger.info("Atualizando pagina da UF %s para a proxima chave", self.config.uf)
            self.bot.atualizar_pagina(self.config.url, espera=self.ESPERA_ATUALIZACAO)

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self._preencher_chave(chave)
        self.bot.esperar(15)
        self._clicar_consultar_ate_resultado()

        # Com a URL confirmada, copia o conteudo inteiro da pagina.
        self.bot.esperar(6)
        self.bot.focar_pagina()
        self.bot.esperar(0.5)

        texto = self.bot.selecionar_tudo_e_copiar().strip()
        if texto:
            logger.info("ES texto copiado -> %s caracteres", len(texto))
            logger.debug("ES previa texto copiado:\n%s", texto[:500])
        else:
            logger.info("ES texto copiado vazio, caindo para OCR")
            texto = self.bot.extrair_texto_pagina("captura_es")

        return self._resultado(
            texto_capturado=texto,
            observacao="Rotina ES executada com clique aleatorio na area do campo e do botao.",
        )

    def _clicar_consultar_ate_resultado(self) -> None:
        for tentativa in range(1, self.MAX_TENTATIVAS + 1):
            logger.info("ES tentativa consulta -> %s", tentativa)
            if tentativa == 1:
                area_botao = self.AREA_BOTAO_PRIMEIRA_TENTATIVA
            else:
                # Depois da primeira tentativa o layout muda: move o mouse para um
                # ponto neutro e procura o botao mais abaixo.
                self.bot.mover_mouse_humano(*self.PONTO_ANTES_BOTAO)
                self.bot.esperar(0.4)
                area_botao = self.AREA_BOTAO_DEMAIS_TENTATIVAS

            x_botao, y_botao = self.bot.ponto_aleatorio(*area_botao)
            logger.info("ES botao consultar -> x=%s, y=%s", x_botao, y_botao)
            self.bot.mover_mouse_humano(x_botao, y_botao)
            self.bot.esperar(0.4)
            self.bot.clicar(x_botao, y_botao)
            self.bot.esperar(4)

            url_atual = self.bot.obter_url_atual()
            logger.info("ES url atual -> %s", url_atual)
            if self.URL_RESULTADO.lower() in url_atual.lower():
                return

        raise TimeoutError(
            f"A consulta do ES nao mudou para a URL de resultado apos {self.MAX_TENTATIVAS} tentativas."
        )

    def _preencher_chave(self, chave: str) -> None:
        x_campo, y_campo = self.bot.ponto_aleatorio(*self.AREA_CAMPO_CHAVE)
        logger.info("ES campo chave -> x=%s, y=%s", x_campo, y_campo)
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.focar_pagina()
        self.bot.esperar(1)
        self.bot.clicar(x_campo, y_campo)
        self.bot.esperar(1)
        self.bot.atalho("ctrl", "a")
        self.bot.colar_texto(chave)
