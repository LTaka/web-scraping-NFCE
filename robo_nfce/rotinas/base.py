import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from robo_nfce.config import ConfigUF

if TYPE_CHECKING:
    from robo_nfce.bot.visual import BotVisual

logger = logging.getLogger(__name__)

MODO_SIMULAR = "simular"
MODO_EXECUTAR = "executar"


class RotinaEstado(ABC):
    """Fluxo base: prepara a pagina da UF e executa os passos da consulta de uma chave.

    Subclasses implementam `_executar_passos` e, se precisarem, sobrescrevem `_preparar_pagina`.
    """

    ESPERA_ATUALIZACAO = 12

    def __init__(self, bot: "BotVisual", config: ConfigUF, modo_execucao: str):
        self.bot = bot
        self.config = config
        self.modo_execucao = modo_execucao
        self.pagina_inicializada = False

    def executar(self, chave: str, linha: dict) -> dict:
        if self.modo_execucao == MODO_SIMULAR:
            return self._resultado_simulado()

        self._preparar_pagina()
        return self._executar_passos(chave, linha)

    @abstractmethod
    def _executar_passos(self, chave: str, linha: dict) -> dict:
        raise NotImplementedError

    def _preparar_pagina(self) -> None:
        """Abre a URL da UF na primeira chave e recarrega nas seguintes."""
        if not self.pagina_inicializada:
            logger.info("Abrindo link da UF %s uma vez: %s", self.config.uf, self.config.url)
            self.bot.abrir_site(self.config.url)
            self._aguardar_ou_falhar(contexto=f"entrada_{self.config.uf.lower()}")
            self.pagina_inicializada = True
        else:
            logger.info("Atualizando pagina da UF %s para a proxima chave", self.config.uf)
            self.bot.atualizar_pagina(self.config.url, espera=self.ESPERA_ATUALIZACAO)
            self._aguardar_ou_falhar(contexto=f"refresh_{self.config.uf.lower()}")

    def _textos_esperados_pagina_inicial(self) -> list[str] | None:
        return None

    def _aguardar_ou_falhar(self, *, contexto: str) -> None:
        textos_esperados = self._textos_esperados_pagina_inicial()
        carregou = self.bot.aguardar_pagina_carregar(
            timeout=20,
            intervalo=1,
            repeticoes_iguais=3,
            textos_esperados=textos_esperados,
            nome_base_arquivo=contexto,
        )
        if not carregou:
            raise TimeoutError(
                f"Nao foi possivel confirmar carregamento da pagina em '{contexto}'. "
                f"Textos esperados: {textos_esperados or 'nenhum'}."
            )

    def _resultado(self, texto_capturado: str, observacao: str, texto_audio: str = "", status: str = "ok") -> dict:
        return {
            "status_robo": status,
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto_capturado,
            "texto_audio": texto_audio,
            "observacao": observacao,
        }

    def _resultado_simulado(self) -> dict:
        return self._resultado(
            texto_capturado="",
            observacao="Rotina nao executada. Use --modo executar para rodar no navegador.",
            status="simulado",
        )
