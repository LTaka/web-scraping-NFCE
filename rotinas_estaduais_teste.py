from abc import ABC, abstractmethod

from bot_visual import BotVisual
from config_ufs import ConfigUF
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


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


URL_MG = "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/consultaarg.xhtml"

def _consultar_nfce_mg_em_pagina(page, chave: str) -> dict:
    try:
        page.goto(URL_MG, wait_until="domcontentloaded", timeout=60000)

        campo = page.locator(
            "input[type='text'], input[name*='chave'], input[id*='chave']"
        ).first
        campo.wait_for(timeout=30000)
        campo.fill(chave)

        botao = page.get_by_role("button").filter(has_text="Consultar").first
        botao.click(timeout=15000)

        page.wait_for_load_state("networkidle", timeout=60000)

        texto = page.locator("body").inner_text(timeout=30000)
        html = page.content()

        return {
            "status_robo": "ok",
            "uf": "MG",
            "texto_capturado": texto,
            "html": html,
            "url_final": page.url,
        }

    except PlaywrightTimeoutError as e:
        return {
            "status_robo": "erro_timeout",
            "uf": "MG",
            "erro": str(e),
            "url_final": page.url,
        }
    except Exception as e:
        return {
            "status_robo": "erro_execucao",
            "uf": "MG",
            "erro": str(e),
            "url_final": page.url,
        }


def consultar_nfce_mg(chave: str) -> dict:
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        try:
            resultado = _consultar_nfce_mg_em_pagina(page, chave)
            if resultado["status_robo"] != "ok":
                page.screenshot(path=f"erro_mg_{chave}.png", full_page=True)
            return resultado
        finally:
            page.close()
            browser.close()


def consultar_com_retry(chave: str, max_tentativas: int = 3) -> dict:
    erros = []

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)

        try:
            for tentativa in range(1, max_tentativas + 1):
                page = browser.new_page()
                try:
                    resultado = _consultar_nfce_mg_em_pagina(page, chave)
                    resultado["tentativa"] = tentativa

                    if resultado["status_robo"] == "ok" and resultado.get("texto_capturado"):
                        return resultado

                    page.screenshot(
                        path=f"erro_mg_{chave}_tentativa_{tentativa}.png",
                        full_page=True,
                    )
                    erros.append(resultado)
                finally:
                    page.close()

            return {
                "status_robo": "falha_mg_instavel",
                "uf": "MG",
                "chave": chave,
                "erros": erros,
                "observacao": "Portal MG instavel apos multiplas tentativas em abas novas do mesmo navegador.",
            }
        finally:
            browser.close()


class RotinaMGPlaywright(RotinaEstado):
    def executar(self, chave: str, linha: dict) -> dict:
        if self.modo_execucao == "simular":
            return {
                "status_robo": "simulado",
                "uf": self.config.uf,
                "url_consulta": self.config.url,
                "texto_capturado": "",
                "texto_audio": "",
                "observacao": "Rotina MG Playwright nao executada. Use --modo executar para rodar no navegador.",
            }

        return self._executar_passos(chave, linha)

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        resultado = consultar_com_retry(chave)
        resultado["uf"] = self.config.uf
        resultado["url_consulta"] = self.config.url
        return resultado
class RotinaMGPadrao(RotinaEstado):
    LARGURA_BASE = 2560
    ALTURA_BASE = 1440
    URLS_RESULTADO_MG = ("http://portalsped.fazenda.mg.gov.br/portalnfce/sistema/consultaarg.xhtml")

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
            print(
                "MG usando a aba atual ja aberta. "
                "Deixe a pagina de consulta pronta e o captcha resolvido antes de continuar."
            )
            self.pagina_inicializada = True

        return self._executar_passos(chave, linha)

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self._preencher_chave_mg(chave)
        self.bot.esperar(10)

        for tentativa in range(1, 6):
            print(f"MG tentativa consulta -> {tentativa}")
            if tentativa > 1:
                x_extra, y_extra = self.bot.escalar_ponto(
                    1919,
                    156,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )
                print(f"MG clique adicional antes do botao -> x={x_extra}, y={y_extra}")
                self.bot.mover_mouse_humano(x_extra, y_extra)
                self.bot.esperar(0.4)
                self.bot.clicar(x_extra, y_extra)
                self.bot.esperar(1.5)

            if tentativa == 1:
                x_botao, y_botao = self.bot.ponto_aleatorio_escalado(
                    2380,
                    2460,
                    380,
                    425,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )
            else:
                x_botao, y_botao = self.bot.ponto_aleatorio_escalado(
                    2380,
                    2460,
                    430,
                    485,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )

            print(f"MG botao consultar -> x={x_botao}, y={y_botao}")
            self.bot.mover_mouse_humano(x_botao, y_botao)
            self.bot.esperar(0.4)
            self.bot.clicar(x_botao, y_botao)
            self.bot.esperar(4)

            url_atual = self.bot.obter_url_atual()
            print(f"MG url atual -> {url_atual}")
            if any(url_resultado.lower() in url_atual.lower() for url_resultado in self.URLS_RESULTADO_MG):
                break

            print("MG URL ainda nao foi para a pagina de resultado, tentando novamente")
        else:
            raise TimeoutError(
                "A consulta do MG nao mudou para a URL de resultado apos 5 tentativas."
            )

        self.bot.esperar(6)
        print("MG focando pagina antes de selecionar tudo")
        self.bot.focar_pagina()
        self.bot.esperar(0.5)

        texto = self.bot.selecionar_tudo_e_copiar().strip()
        if texto:
            print(f"MG texto copiado -> {len(texto)} caracteres")
            print("MG previa texto copiado:")
            print(texto[:500])
        else:
            print("MG texto copiado vazio, caindo para OCR")

        if not texto:
            texto = self.bot.extrair_texto_pagina("captura_mg")
        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto,
            "texto_audio": "",
            "observacao": "Rotina MG validada pela URL de resultado, no mesmo padrao do ES.",
        }

    def _preencher_chave_mg(self, chave: str):
        x_campo, y_campo = self.bot.ponto_aleatorio_escalado(
            1860,
            2445,
            380,
            425,
            self.LARGURA_BASE,
            self.ALTURA_BASE,
        )
        print(f"MG campo chave -> x={x_campo}, y={y_campo}")
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.clicar(x_campo, y_campo)
        self.bot.esperar(0.3)
        self.bot.atalho("ctrl", "a")
        self.bot.colar_texto(chave)


class RotinaESPadrao(RotinaEstado):
    LARGURA_BASE = 1366
    ALTURA_BASE = 768
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

                x_extra, y_extra = self.bot.escalar_ponto(
                    1190,
                    492,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )
                self.bot.mover_mouse_humano(x_extra, y_extra)
                self.bot.esperar(0.4)
            if tentativa == 1:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 442, 479) segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio_escalado(
                    376,
                    495,
                    476,
                    512,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )
            else:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 523, 550)  segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio_escalado(
                    393,
                    492,
                    548,
                    588,
                    self.LARGURA_BASE,
                    self.ALTURA_BASE,
                )
      
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

        x_campo, y_campo = self.bot.ponto_aleatorio_escalado(
            393,
            1138,
            387,
            452,
            self.LARGURA_BASE,
            self.ALTURA_BASE,
        )
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
