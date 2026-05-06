from abc import ABC, abstractmethod

from bot_visual import BotVisual
from config_ufs import ConfigUF


class RotinaEstado(ABC):
    def __init__(self, bot: BotVisual, config: ConfigUF, modo_execucao: str):
        self.bot = bot
        self.config = config
        self.modo_execucao = modo_execucao
        self.pagina_inicializada = False
        self.primeira_execucao = True

    def _aguardar_ou_falhar(self, *, contexto: str, textos_esperados: list[str] | None = None):
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

    def executar(self, chave: str, linha: dict) -> dict:
        if self.modo_execucao == "simular":
            return {
                "status_robo": "simulado",
                "uf": self.config.uf,
                "url_consulta": self.config.url,
                "texto_capturado": "",
                "texto_audio": "",
                "observacao": "Rotina nao executada. Use --modo executar para rodar no navegador.",
            }

        if not self.pagina_inicializada:
            print(f"Abrindo link da UF {self.config.uf} uma vez: {self.config.url}")
            self.bot.abrir_site(self.config.url)
            self._aguardar_ou_falhar(
                contexto=f"entrada_{self.config.uf.lower()}",
                textos_esperados=self._textos_esperados_pagina_inicial(),
            )
            self.pagina_inicializada = True
        else:
            print(f"Atualizando pagina da UF {self.config.uf} para a proxima chave")
            self.bot.atualizar_pagina(espera=12)
            self._aguardar_ou_falhar(
                contexto=f"refresh_{self.config.uf.lower()}",
                textos_esperados=self._textos_esperados_pagina_inicial(),
            )

        return self._executar_passos(chave, linha)

    @abstractmethod
    def _executar_passos(self, chave: str, linha: dict) -> dict:
        raise NotImplementedError

    def _textos_esperados_pagina_inicial(self) -> list[str] | None:
        return None


class RotinaMGPadrao(RotinaEstado):
    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self.bot.esperar(2)

        # Ajuste os cliques e campos abaixo conforme o site de MG.
        # Exemplo:
        # self.bot.clicar(400, 320)
        # Point(x=1919, y=156)
        # Point(x=2441, y=402)
        # self.bot.escrever(chave)
        # self.bot.pressionar("enter")
        # texto = self.bot.ler_area_da_tela(300, 250, 900, 500)

        texto = self.bot.extrair_texto_pagina("captura_mg")
        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto,
            "texto_audio": "",
            "observacao": "Preencha os cliques da rotina MG em rotinas_estaduais.py.",
        }


class RotinaESPadrao(RotinaEstado):
    URL_RESULTADO_ES = "https://app.sefaz.es.gov.br/ConsultaNFCe/ConsultaDANFE_NFCe.aspx"

    def executar(self, chave: str, linha: dict) -> dict:
        if self.modo_execucao == "simular":
            return {
                "status_robo": "simulado",
                "uf": self.config.uf,
                "url_consulta": self.config.url,
                "texto_capturado": "",
                "texto_audio": "",
                "observacao": "Rotina nao executada. Use --modo executar para rodar no navegador.",
            }

        if not self.pagina_inicializada:
            print(f"Abrindo link da UF {self.config.uf} uma vez: {self.config.url}")
            self.bot.abrir_site(self.config.url)
            self.pagina_inicializada = True
        else:
            print(f"Atualizando pagina da UF {self.config.uf} para a proxima chave")
            self.bot.atualizar_pagina(self.config.url, espera=12)

        return self._executar_passos(chave, linha)

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self._preencher_chave_es(chave)
        self.bot.esperar(10)

        for tentativa in range(1, 6):
            print(f"ES tentativa consulta -> {tentativa}")
            if tentativa > 1:
                print("ES clique extra antes do botao -> x=2473, y=452")
                # self.bot.mover_mouse_humano(2473, 452) segunda tela  27pol

                self.bot.mover_mouse_humano(1190, 492)
                self.bot.esperar(0.4)
            if tentativa == 1:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 442, 479) segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(376, 495, 476, 512)
            else:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 523, 550)  segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(393, 492, 548, 588)
      
            print(f"ES botao consultar -> x={x_botao}, y={y_botao}")
            self.bot.mover_mouse_humano(x_botao, y_botao)
            self.bot.esperar(0.4)
            self.bot.clicar(x_botao, y_botao)
            self.bot.esperar(4)

            url_atual = self.bot.obter_url_atual()
            print(f"ES url atual -> {url_atual}")
            if self.URL_RESULTADO_ES.lower() in url_atual.lower():
                break
        else:
            raise TimeoutError(
                "A consulta do ES nao mudou para a URL de resultado apos 5 tentativas."
            )

        self.bot.esperar(6)
        print("ES focando pagina antes de selecionar tudo")
        self.bot.focar_pagina()
        self.bot.esperar(0.5)

        texto = self.bot.selecionar_tudo_e_copiar().strip()
        if texto:
            print(f"ES texto copiado -> {len(texto)} caracteres")
            print("ES previa texto copiado:")
            print(texto[:500])
        else:
            print("ES texto copiado vazio, caindo para OCR")
        if not texto:
            texto = self.bot.extrair_texto_pagina("captura_es")
        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto,
            "texto_audio": "",
            "observacao": "Rotina ES executada com clique aleatorio na area do campo e do botao.",
        }

    def _preencher_chave_es(self, chave: str):
        # x_campo, y_campo = self.bot.ponto_aleatorio(1672, 2419, 349, 418) segunda tela 27pol

        x_campo, y_campo = self.bot.ponto_aleatorio(393, 1138, 387, 452)
        print(f"ES campo chave -> x={x_campo}, y={y_campo}")
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.clicar(x_campo, y_campo)
        self.bot.esperar(0.3)
        self.bot.atalho("ctrl", "a")
        self.bot.colar_texto(chave)


class RotinaSPComAudio(RotinaEstado):
    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self.bot.esperar(2)

        # Exemplo do fluxo que voce descreveu:
        # 1. clica em um ponto que ativa o audio
        # 2. escuta o microfone
        # 3. escreve o texto escutado em outro campo
        # 4. clica em consultar
        # 5. copia as informacoes da tela
        #
        # Ajuste as coordenadas conforme seu navegador/site:
        # texto_audio = self.bot.clicar_ouvir_e_escrever(
        #     x_clicar=760,
        #     y_clicar=410,
        #     x_escrever=545,
        #     y_escrever=412,
        # )
        # self.bot.clicar(820, 510)
        # self.bot.esperar(2)
        # texto_tela = self.bot.copiar_area_da_tela(220, 180, 1100, 700, "captura_sp.png")

        texto_audio = self.bot.ouvir_microfone()
        texto_tela = self.bot.extrair_texto_pagina("captura_sp")

        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto_tela,
            "texto_audio": texto_audio,
            "observacao": "Ajuste as coordenadas da rotina SP com audio em rotinas_estaduais.py.",
        }


class RotinaBAComAudio(RotinaSPComAudio):
    pass


class RotinaRJPadrao(RotinaESPadrao):
    pass


def criar_rotina(bot: BotVisual, config: ConfigUF, modo_execucao: str) -> RotinaEstado:
    rotinas = {
        "mg_padrao": RotinaMGPadrao,
        "es_padrao": RotinaESPadrao,
        "sp_com_audio": RotinaSPComAudio,
        "ba_com_audio": RotinaBAComAudio,
        "rj_padrao": RotinaRJPadrao,
    }

    try:
        classe_rotina = rotinas[config.rotina]
    except KeyError as erro:
        raise KeyError(f"Rotina {config.rotina} nao encontrada para a UF {config.uf}.") from erro

    return classe_rotina(bot, config, modo_execucao)
