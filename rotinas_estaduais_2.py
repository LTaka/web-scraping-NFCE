import re
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
    TEXTO_SUCESSO_MG = "Produtos e Serviços"
    CABECALHO_TABELA_MG = (
        "Número",
        "Descrição",
        "Quantidade",
        "Unidade Comercial",
        "Valor Unitário",
        "Valor(R$)",
    )

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self._preencher_chave_mg(chave)
        self.bot.esperar(10)
        texto = ""
        for tentativa in range(1, 6):
            print(f"MG tentativa consulta -> {tentativa}")
            if tentativa > 1:
                print("MG clique adicional antes do botao -> x=285, y=495")
                self.bot.mover_mouse_humano(285, 495)
                self.bot.esperar(0.4)
                self.bot.clicar(285, 495)
                self.bot.esperar(1.5)

            if tentativa == 1:
                x_botao, y_botao = self.bot.ponto_aleatorio(261, 454, 505, 529)
            else:
                x_botao, y_botao = self.bot.ponto_aleatorio(260, 454, 554, 576)

            print(f"MG botao consultar -> x={x_botao}, y={y_botao}")
            self.bot.mover_mouse_humano(x_botao, y_botao)
            self.bot.esperar(0.4)
            self.bot.clicar(x_botao, y_botao)
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
                print("MG texto copiado vazio nesta tentativa")

            bloco_produtos = self._extrair_bloco_produtos_mg(texto)
            if self._texto_tem_tabela_produtos_mg(texto):
                print("MG confirmou cabecalho e itens de 'Produtos e Serviços' no texto copiado")
                if bloco_produtos:
                    print("MG bloco de produtos detectado:")
                    print(bloco_produtos[:500])
                self._reiniciar_aba_consulta()
                break

            print("MG texto ainda sem a tabela de produtos de MG, tentando novamente")
        else:
            print("MG nao confirmou pelo clipboard, caindo para OCR")
            texto = ""
    
        if not texto:
            texto = self.bot.extrair_texto_pagina("captura_mg")
        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto,
            "texto_audio": "",
            "observacao": "Rotina MG validada pelo texto copiado contendo a tabela de 'Produtos e Servicos'.",
        }

    def _preencher_chave_mg(self, chave: str):
        x_campo, y_campo = self.bot.ponto_aleatorio(265, 766, 392, 411)
        print(f"MG campo chave -> x={x_campo}, y={y_campo}")
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.clicar(x_campo, y_campo)
        self.bot.esperar(0.3)
        self.bot.atalho("ctrl", "a")
        self.bot.colar_texto(chave)

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

    def _texto_tem_tabela_produtos_mg(self, texto: str) -> bool:
        if not texto:
            return False

        texto_normalizado = texto.replace("\r\n", "\n").replace("\r", "\n")
        if not all(cabecalho in texto_normalizado for cabecalho in self.CABECALHO_TABELA_MG):
            return False

        padrao_item = re.compile(
            r"^\s*\d+\s+.+?\s+\d+(?:[.,]\d+)?\s+[A-Za-z]+\s+R\$\s*\d+[.,]\d{2}\s+R\$\s*\d+[.,]\d{2}\s*$"
        )
        return any(padrao_item.match(linha.strip()) for linha in texto_normalizado.splitlines())

    def _extrair_bloco_produtos_mg(self, texto: str) -> str:
        if not texto:
            return ""

        texto_normalizado = texto.replace("\r\n", "\n").replace("\r", "\n")
        inicio = texto_normalizado.find("Produtos e Serviços")
        if inicio < 0:
            return ""

        fim = texto_normalizado.find("Situação atual:", inicio)
        if fim < 0:
            fim = len(texto_normalizado)

        bloco = texto_normalizado[inicio:fim].strip()
        return bloco if "Valor(R$)" in bloco else ""

    def _reiniciar_aba_consulta(self):
        print("MG consulta concluida com sucesso, reiniciando a aba para a proxima chave")
        self.bot.atalho("ctrl", "w")
        self.bot.esperar(0.8)
        self.bot.atalho("ctrl", "t")
        self.bot.esperar(0.8)
        self.bot.abrir_site(self.config.url, espera=12)
        self.pagina_inicializada = True


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
        self.bot.esperar(15)

        for tentativa in range(1, 6):
            print(f"ES tentativa consulta -> {tentativa}")
            if tentativa > 1:
                print("ES clique extra antes do botao -> x=2473, y=452")
                # self.bot.mover_mouse_humano(2473, 452) segunda tela  27pol

                self.bot.mover_mouse_humano(890, 419)
                self.bot.esperar(0.4)
            if tentativa == 1:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 442, 479) segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(174, 266, 407, 442)
            else:
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 523, 550)  segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(174, 266, 475, 505)
      
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

        x_campo, y_campo = self.bot.ponto_aleatorio(172, 840, 339, 390)
        print(f"ES campo chave -> x={x_campo}, y={y_campo}")
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        self.bot.focar_pagina()
        self.bot.esperar(1)

        self.bot.clicar(x_campo, y_campo)
        self.bot.esperar(1)

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
