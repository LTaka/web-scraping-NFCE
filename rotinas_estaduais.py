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
    URL_INICIAL_MG = "https://portalsped.fazenda.mg.gov.br/portalnfce/sistema/consultaarg.xhtml"

    AREA_CAMPO_CHAVE_INICIAL_MG = (1651, 2365, 403, 408)
    AREA_CAMPO_CHAVE_ERRO_MG = (1651, 2365, 452, 452)
    AREA_BOTAO_CONSULTAR_INICIAL_MG = (1642, 1923, 435, 463)
    AREA_BOTAO_CONSULTAR_ERRO_MG = (1642, 1923, 485, 508)
    TEXTO_SUCESSO_MG = "Produtos e Serviços"

    TEXTO_RESULTADO_MG = "Consulta Resumida - Ambiente de Produção"
    FRAGMENTOS_PAGINA_INICIAL_MG = (
        "Intranet SEF - Secretaria de Estado de Fazenda",
        "Consultar NFC-e",
        "Consultar Inutilização",
        "Nota Fiscal de Consumidor Eletrônica (NFC-e) - Ambiente de Produção",
        "Observações",
        "1. Chave de Acesso deve ser informado o número de 44 dígitos NFC-e (Nota Fiscal de Consumidor Eletrônica)",
        "reCAPTCHA",
        "Consulta Nota Fiscal de Consumidor Eletrônica (NFC-e)",
        "Chave de acesso",
        "Versão 1.2.20",
        "Rodovia Papa João Paulo II, 4.001 - Prédio Gerais (6º e 7º andares) - Bairro Serra Verde, Belo Horizonte/MG CEP 31630-901",
    )
    LIMITE_EXCEDENTE_PAGINA_INICIAL_MG = 120
    ESTADOS_CONSULTA_RECUPERAVEIS_MG = {
        "inicial",
        "erro"
    }
    CABECALHO_TABELA_MG = (
        "Número",
        "Descrição",
        "Quantidade",
        "Unidade Comercial",
        "Valor Unitário",
        "Valor(R$)",
    )

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        # A primeira tentativa sempre parte do layout inicial da consulta.
        print("MG iniciando execucao da chave atual")
        print(f"MG chave recebida -> {chave}")
        x_campo, y_campo = self._ponto_campo_chave_mg("inicial")
        self._preencher_chave_mg(chave, x_campo, y_campo)
        self.bot.esperar(4)
        texto = ""
        for tentativa in range(1, 6):
            print(f"MG tentativa consulta -> {tentativa}")

            # Antes de cada clique, a rotina copia o texto atual da pagina para
            # decidir em qual layout esta: tela inicial, tela com erro validavel,
            # resultado, ou estado desconhecido.
   
            estado_antes = self._ler_estado_pagina_mg()
            print(f"MG estado antes do clique consultar -> {estado_antes}")
            print(f"MG tentativa {tentativa}: iniciando preparacao do clique")


            # if tentativa > 1 and estado_antes == "erro_captcha":
            #     print("MG clique adicional antes do botao -> x=285, y=495")
            #     self.bot.mover_mouse_humano(285, 495)
            #     self.bot.esperar(0.2)
            #     self.bot.clicar(285, 495)
            #     self.bot.esperar(0.5)

            if  estado_antes == "inicial":
                # Layout da tela inicial:
                # 1. usa a area normal do campo
                # 2. usa a area normal do botao consultar
                print("MG layout escolhido antes do clique -> inicial")
                print("MG nova tentativa ainda na tela inicial; repreenchendo a chave")
                x_campo, y_campo = self._ponto_campo_chave_mg("inicial")
                self._preencher_chave_mg(chave, x_campo, y_campo)
                x_botao, y_botao = self._ponto_botao_consultar_mg("inicial")
            elif estado_antes == "erro":
                # Layout de erro:
                # Quando a pagina base da consulta reaparece com conteudo extra,
                # assume que o layout foi deslocado pela mensagem de erro.
                print(f"MG layout escolhido antes do clique -> erro ({estado_antes})")
                x_campo, y_campo = self._ponto_campo_chave_mg(estado_antes)
                self._preencher_chave_mg(chave, x_campo, y_campo)
                x_botao, y_botao = self._ponto_botao_consultar_mg(estado_antes)
            else:
                # Qualquer texto fora dos estados conhecidos e tratado como tela
                # corrompida ou fora do fluxo. Nessa situacao a aba e recriada.
                print("MG estado fora do fluxo esperado antes do clique; reiniciando pagina inicial")
                self._reiniciar_aba_consulta()
                x_campo, y_campo = self._ponto_campo_chave_mg("inicial")
                self._preencher_chave_mg(chave, x_campo, y_campo)
                self.bot.esperar(2)
                x_botao, y_botao = self._ponto_botao_consultar_mg("inicial")

            print(f"MG botao consultar -> x={x_botao}, y={y_botao}")
            print("MG movendo mouse para o botao consultar")
            self.bot.mover_mouse_humano(x_botao, y_botao)
            # self.bot.esperar(0.4)
            print("MG clicando no botao consultar")
            self.bot.clicar(x_botao, y_botao)
            self.bot.esperar(4)


            print("MG focando pagina antes de selecionar tudo")
            self.bot.focar_pagina()
            self.bot.esperar(0.3)

            print("MG executando Ctrl+A / Ctrl+C para ler a pagina")
            texto = self.bot.selecionar_tudo_e_copiar().strip()
            if texto:
                print(f"MG texto copiado -> {len(texto)} caracteres")
                print("MG previa texto copiado:")
                print(texto[:500])
            else:
                print("MG texto copiado vazio nesta tentativa")

            # Depois de copiar a pagina inteira com Ctrl+A/Ctrl+C, classifica
            # novamente o estado. Se nao reconhecer o texto, reinicia a aba.
            estado_depois = self._ler_estado_pagina_mg(texto)
            print(f"MG estado apos consultar -> {estado_depois}")
            if self._estado_exige_reinicio_mg(estado_depois):
                print("MG texto apos consultar nao corresponde a nenhum estado esperado; reiniciando aba")
                self._reiniciar_aba_consulta()
                x_campo, y_campo = self._ponto_campo_chave_mg("inicial")
                self._preencher_chave_mg(chave, x_campo, y_campo)
                self.bot.esperar(2)
                texto = ""
                continue

            # Para acelerar o fluxo, considera sucesso quando o texto copiado ja
            # contem a secao "Produtos e Servicos". Nessa hora ja salva o texto
            # e prepara a pagina inicial para a proxima chave.
            if self._texto_eh_resultado_mg(texto):
                print("MG confirmou resultado pelo texto copiado")
                print("MG encerrando a tentativa atual com sucesso e preparando a proxima chave")
                self._reiniciar_aba_consulta()
                break

            # Se o texto ainda for da propria tela inicial ou de um erro
            # recuperavel, basta seguir para a proxima tentativa sem checar URL.
            print("MG texto ainda esta em tela inicial/erro recuperavel, tentando novamente")
        else:
            print("MG nao confirmou pelo clipboard, caindo para OCR")
            texto = ""
    
        if not texto:
            print("MG executando OCR como ultimo recurso")
            texto = self.bot.extrair_texto_pagina("captura_mg")
            print(f"MG OCR retornou -> {len(texto)} caracteres")
        print("MG finalizando execucao da chave atual")
        return {
            "status_robo": "ok",
            "uf": self.config.uf,
            "url_consulta": self.config.url,
            "texto_capturado": texto,
            "texto_audio": "",
            "observacao": "Rotina MG validada pelo texto copiado contendo a tabela de 'Produtos e Servicos'.",
        }

    def _preencher_chave_mg(self, chave: str,x_campo:int,y_campo:int):
        print(f"MG campo chave -> x={x_campo}, y={y_campo}")
        print("MG movendo mouse para o campo da chave")
        self.bot.mover_mouse_humano(x_campo, y_campo)
        self.bot.esperar(0.4)
        print("MG clicando no campo da chave")
        self.bot.clicar(x_campo, y_campo)
        print("MG limpando o campo com Ctrl+A")
        self.bot.atalho("ctrl", "a")
        print("MG colando a chave no campo")
        self.bot.colar_texto(chave)

    def _abrir_pagina_inicial_mg(self, espera: int = 12):
        print(f"MG abrindo URL inicial fixa: {self.URL_INICIAL_MG}")

        for tentativa in range(1, 4):
            print(f"MG tentativa de navegar para pagina inicial -> {tentativa}")
            print("MG enviando a URL inicial para a barra de enderecos")
            self.bot.abrir_site(self.URL_INICIAL_MG, espera=espera)

            url_atual = self.bot.obter_url_atual()
            print(f"MG URL atual apos enviar link -> {url_atual}")
            if self._url_atual_eh_inicial_mg(url_atual):
                print("MG confirmou a URL inicial na barra de enderecos")
                return

        raise TimeoutError(
            "MG nao mudou para a URL inicial apos 3 tentativas de envio do link."
        )

    def _normalizar_url_mg(self, url: str) -> str:
        return (url or "").strip().rstrip("/").lower()

    def _estado_usa_layout_erro_mg(self, estado: str) -> bool:
        print(f"MG verificando se o estado usa layout de erro -> {estado}")
        return estado == "erro"

    def _ponto_campo_chave_mg(self, estado: str) -> tuple[int, int]:
        # Quando ha erro visivel na pagina, o campo da chave sai do layout
        # inicial e passa a usar outra faixa vertical.
        if self._estado_usa_layout_erro_mg(estado):
            area = self.AREA_CAMPO_CHAVE_ERRO_MG
        else:
            area = self.AREA_CAMPO_CHAVE_INICIAL_MG
        print(f"MG area escolhida para campo da chave -> {area} (estado={estado})")
        return self.bot.ponto_aleatorio(*area)

    def _ponto_botao_consultar_mg(self, estado: str) -> tuple[int, int]:
        # O botao tambem muda de posicao quando a pagina entra no layout de erro.
        if self._estado_usa_layout_erro_mg(estado):
            area = self.AREA_BOTAO_CONSULTAR_ERRO_MG
        else:
            area = self.AREA_BOTAO_CONSULTAR_INICIAL_MG
        print(f"MG area escolhida para botao consultar -> {area} (estado={estado})")
        return self.bot.ponto_aleatorio(*area)

    def _texto_normalizado_mg(self, texto: str) -> str:
        return " ".join((texto or "").lower().split())

    def _texto_tem_fragmentos_pagina_inicial_mg(self, texto: str) -> bool:
        texto_normalizado = self._texto_normalizado_mg(texto)
        return all(fragmento.lower() in texto_normalizado for fragmento in self.FRAGMENTOS_PAGINA_INICIAL_MG)

    def _texto_excedente_layout_inicial_mg(self, texto: str) -> str:
        excedente = self._texto_normalizado_mg(texto)
        for fragmento in self.FRAGMENTOS_PAGINA_INICIAL_MG:
            excedente = excedente.replace(fragmento.lower(), " ")
        return " ".join(excedente.split())

    def _texto_eh_pagina_inicial_mg(self, texto: str) -> bool:
        if not self._texto_tem_fragmentos_pagina_inicial_mg(texto):
            return False
        excedente = self._texto_excedente_layout_inicial_mg(texto)
        print(f"MG excedente apos remover fragmentos da pagina inicial -> {len(excedente)} caracteres")
        return len(excedente) <= self.LIMITE_EXCEDENTE_PAGINA_INICIAL_MG

    def _texto_eh_pagina_erro_mg(self, texto: str) -> bool:
        if not self._texto_tem_fragmentos_pagina_inicial_mg(texto):
            return False
        excedente = self._texto_excedente_layout_inicial_mg(texto)
        print(f"MG excedente identificado para layout de erro -> {len(excedente)} caracteres")
        return len(excedente) > self.LIMITE_EXCEDENTE_PAGINA_INICIAL_MG

    def _texto_eh_resultado_mg(self, texto: str) -> bool:
        texto_normalizado = (texto or "").lower()
        return self.TEXTO_RESULTADO_MG.lower() in texto_normalizado or self.TEXTO_SUCESSO_MG.lower() in texto_normalizado

    def _copiar_texto_pagina_mg(self) -> str:
        print("MG focando pagina para copiar o texto completo")
        self.bot.focar_pagina()
        print("MG executando Ctrl+A / Ctrl+C para leitura de estado")
        texto = self.bot.selecionar_tudo_e_copiar().strip()
        print(f"MG texto usado para leitura de estado -> {len(texto)} caracteres")
        return texto

    def _ler_estado_pagina_mg(self, texto: str | None = None) -> str:
        if texto is None:
            print("MG lendo estado da pagina com novo clipboard")
            texto = self._copiar_texto_pagina_mg()
        else:
            print(f"MG lendo estado com texto ja fornecido -> {len(texto)} caracteres")

        if self._texto_eh_resultado_mg(texto):
            print("MG classificacao de estado -> resultado")
            return "resultado"
        if self._texto_eh_pagina_erro_mg(texto):
            print("MG classificacao de estado -> erro")
            return "erro"
        if self._texto_eh_pagina_inicial_mg(texto):
            print("MG classificacao de estado -> inicial")
            return "inicial"
        print("MG classificacao de estado -> desconhecido")
        return "desconhecido"

    def _url_atual_eh_inicial_mg(self, url: str) -> bool:
        return self._normalizar_url_mg(url) == self._normalizar_url_mg(self.URL_INICIAL_MG)


    def _estado_exige_reinicio_mg(self, estado: str) -> bool:
        exige_reinicio = estado not in self.ESTADOS_CONSULTA_RECUPERAVEIS_MG and estado != "resultado"
        print(f"MG estado exige reinicio? -> {exige_reinicio} (estado={estado})")
        return exige_reinicio

    def _garantir_pagina_inicial_mg(self, espera: int = 12, max_tentativas: int = 4):
        print(f"MG garantindo pagina inicial -> pagina_inicializada={self.pagina_inicializada}")

        for tentativa in range(1, max_tentativas + 1):
            print(f"MG tentativa de garantir pagina inicial -> {tentativa}/{max_tentativas}")
            url_atual = self.bot.obter_url_atual()
            print(f"MG URL atual antes da validacao da tela inicial -> {url_atual}")

            if tentativa == 1 and self._url_atual_eh_inicial_mg(url_atual):
                print("MG URL atual ja aponta para a pagina inicial; validando o conteudo")
            else:
                print("MG reenviando URL inicial e recarregando para forcar a tela correta")
                self.bot.abrir_site(self.URL_INICIAL_MG, espera=espera)
                self.bot.atualizar_pagina(self.URL_INICIAL_MG, espera=espera)

            texto_inicial = self._copiar_texto_pagina_mg()
            estado_inicial = self._ler_estado_pagina_mg(texto_inicial)
            print(f"MG estado apos tentativa de preparar pagina inicial -> {estado_inicial}")

            if estado_inicial == "inicial":
                print("MG confirmou a tela inicial correta")
                return

            print("MG tela inicial ainda nao confirmou; nova tentativa sera executada")

        raise TimeoutError("MG nao confirmou a tela inicial correta apos varias tentativas de recarga.")

    def executar(self, chave: str, linha: dict) -> dict:
        print("MG metodo executar chamado")
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
            print(f"Abrindo link da UF {self.config.uf} uma vez: {self.URL_INICIAL_MG}")
        else:
            print(f"Verificando pagina inicial da UF {self.config.uf} para a proxima chave")

        self._garantir_pagina_inicial_mg()
        self.pagina_inicializada = True
        print("MG pagina inicial pronta; iniciando fluxo da consulta")

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
        # Reinicia mais rapido recarregando a URL inicial na mesma aba.
        print("MG reiniciando fluxo pela URL inicial")
        self._garantir_pagina_inicial_mg(espera=3, max_tentativas=4)
        self.pagina_inicializada = True
        print("MG fluxo reposicionado na pagina inicial")


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
        # O fluxo do ES comeca colando a chave no campo atual da pagina.
        self._preencher_chave_es(chave)
        self.bot.esperar(15)

        for tentativa in range(1, 6):
            print(f"ES tentativa consulta -> {tentativa}")
            if tentativa > 1:
                # Depois da primeira tentativa, o layout muda e a rotina faz um
                # clique extra antes de procurar o botao consultar novamente.
                print("ES clique extra antes do botao -> x=2473, y=452")
                # self.bot.mover_mouse_humano(2473, 452) segunda tela  27pol

                self.bot.mover_mouse_humano(890, 419)
                self.bot.esperar(0.4)
            if tentativa == 1:
                # Primeira tentativa: usa a faixa normal do botao.
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 442, 479) segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(174, 266, 407, 442)
            else:
                # Tentativas seguintes: o botao costuma aparecer mais abaixo.
                # x_botao, y_botao = self.bot.ponto_aleatorio(1674, 1778, 523, 550)  segunda tela  27pol
                x_botao, y_botao = self.bot.ponto_aleatorio(174, 266, 475, 505)
      
            print(f"ES botao consultar -> x={x_botao}, y={y_botao}")
            self.bot.mover_mouse_humano(x_botao, y_botao)
            self.bot.esperar(0.4)
            self.bot.clicar(x_botao, y_botao)
            self.bot.esperar(4)

            # O ES considera sucesso de navegacao quando a URL muda para a
            # pagina final de resultado.
            url_atual = self.bot.obter_url_atual()
            print(f"ES url atual -> {url_atual}")
            if self.URL_RESULTADO_ES.lower() in url_atual.lower():
                break
        else:
            raise TimeoutError(
                "A consulta do ES nao mudou para a URL de resultado apos 5 tentativas."
            )

        # Com a URL confirmada, foca a pagina e copia o conteudo inteiro usando
        # Ctrl+A/Ctrl+C para registrar o texto retornado pelo portal.
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
            # Se o clipboard nao trouxer texto, usa OCR como fallback.
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
        # O clique no campo usa uma faixa aleatoria antes de selecionar tudo e
        # colar a chave.
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
