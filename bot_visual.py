import hashlib
import math
import random
import time
from pathlib import Path
import tkinter as tk

import pyautogui
import pyperclip
import pytesseract
import speech_recognition as sr
from PIL import Image
from pyperclip import PyperclipException

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5


class BotVisual:
    def __init__(self):
        self.print_posicao_mouse()

    def print_posicao_mouse(self):
        print("Mova o mouse para o canto superior esquerdo para parar o robô.")
        print("Posição atual:", pyautogui.position())

    def esperar(self, segundos=2):
        time.sleep(segundos)

    def copiar_para_area_transferencia(self, texto: str) -> bool:
        try:
            pyperclip.copy(texto)
            return True
        except PyperclipException:
            pass

        try:
            raiz = tk.Tk()
            raiz.withdraw()
            raiz.clipboard_clear()
            raiz.clipboard_append(texto)
            raiz.update()
            raiz.destroy()
            return True
        except tk.TclError:
            return False

    def ler_area_transferencia(self) -> str:
        try:
            return pyperclip.paste()
        except PyperclipException:
            pass

        try:
            raiz = tk.Tk()
            raiz.withdraw()
            texto = raiz.clipboard_get()
            raiz.destroy()
            return texto
        except tk.TclError:
            return ""

    def abrir_site(self, url: str, espera=1):
        pyautogui.hotkey("ctrl", "l")
        self.esperar(0.2)
        pyautogui.hotkey("ctrl", "a")
        self.esperar(0.1)
        self.escrever(url)
        pyautogui.press("enter")
        self.esperar(espera)

    def atualizar_pagina(self, url: str, espera=2):
        self.abrir_site(url, espera=espera)

    def obter_url_atual(self) -> str:
        pyautogui.hotkey("ctrl", "l")
        self.esperar(0.2)
        pyautogui.hotkey("ctrl", "c")
        self.esperar(0.2)
        url = self.ler_area_transferencia().strip()
        pyautogui.press("esc")
        self.esperar(0.1)
        return url

    def focar_pagina(self, proporcao_x=0.5, proporcao_y=0.45, espera=0.3):
        largura, altura = pyautogui.size()
        x = int(largura * proporcao_x)
        y = int(altura * proporcao_y)
        self.mover_mouse_humano(x, y)
        self.esperar(espera)
        self.clicar(x, y)

    def clicar(self, x: int, y: int, clicks=1, intervalo=0.25):
        pyautogui.click(x, y, clicks=clicks, interval=intervalo)

    def mover_mouse_humano(self, x: int, y: int, duracao_min=0.4, duracao_max=1.2):
        posicao_atual = pyautogui.position()
        x_atual, y_atual = posicao_atual.x, posicao_atual.y
        distancia = math.hypot(x - x_atual, y - y_atual)
        duracao_total = random.uniform(duracao_min, duracao_max)
        duracao_total = max(duracao_total, min(2.0, distancia / 900))
        passos = max(4, min(10, int(distancia / 250) + 3))

        for passo in range(1, passos + 1):
            progresso = passo / passos
            curva = 3 * (progresso ** 2) - 2 * (progresso ** 3)
            desvio_x = random.uniform(-6, 6) * (1 - progresso)
            desvio_y = random.uniform(-6, 6) * (1 - progresso)
            destino_x = x_atual + (x - x_atual) * curva + desvio_x
            destino_y = y_atual + (y - y_atual) * curva + desvio_y
            if passo == passos:
                destino_x = x
                destino_y = y

            duracao_passo = duracao_total / passos
            duracao_passo *= random.uniform(0.75, 1.35)
            pyautogui.moveTo(destino_x, destino_y, duration=duracao_passo, tween=pyautogui.linear)

    def ponto_aleatorio(self, x_min: int, x_max: int, y_min: int, y_max: int) -> tuple[int, int]:
        return random.randint(x_min, x_max), random.randint(y_min, y_max)

    def mover_e_clicar_em_area(
        self,
        x_min: int,
        x_max: int,
        y_min: int,
        y_max: int,
        clicks=1,
        intervalo=0.25,
        espera=0.3,
    ) -> tuple[int, int]:
        x, y = self.ponto_aleatorio(x_min, x_max, y_min, y_max)
        self.mover_mouse_humano(x, y)
        self.esperar(espera)
        self.clicar(x, y, clicks=clicks, intervalo=intervalo)
        return x, y

    def arrastar(self, x_inicial: int, y_inicial: int, x_final: int, y_final: int, duracao=0.3):
        pyautogui.moveTo(x_inicial, y_inicial)
        pyautogui.dragTo(x_final, y_final, duration=duracao, button="left")

    def rolar(self, cliques: int):
        pyautogui.scroll(cliques)

    def pressionar(self, tecla: str):
        pyautogui.press(tecla)

    def atalho(self, *teclas: str):
        pyautogui.hotkey(*teclas)

    def escrever(self, texto: str):
        if self.copiar_para_area_transferencia(texto):
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(texto, interval=0.02)

    def colar_texto(self, texto: str):
        if not self.copiar_para_area_transferencia(texto):
            raise RuntimeError(
                "Nao foi possivel copiar para a area de transferencia. "
                "A chave precisa ser colada, nao digitada."
            )
        pyautogui.hotkey("ctrl", "v")

    def clicar_e_escrever(self, x: int, y: int, texto: str, espera=0.5):
        self.clicar(x, y)
        self.esperar(espera)
        self.escrever(texto)

    def mover_clicar_e_escrever_em_area(
        self,
        x_min: int,
        x_max: int,
        y_min: int,
        y_max: int,
        texto: str,
        espera=0.5,
    ) -> tuple[int, int]:
        x, y = self.mover_e_clicar_em_area(x_min, x_max, y_min, y_max, espera=espera)
        self.atalho("ctrl", "a")
        self.escrever(texto)
        return x, y

    def clicar_ouvir_e_escrever(
        self,
        x_clicar: int,
        y_clicar: int,
        x_escrever: int,
        y_escrever: int,
        timeout=10,
        phrase_time_limit=20,
        espera=0.5,
    ) -> str:
        self.clicar(x_clicar, y_clicar)
        self.esperar(espera)
        texto = self.ouvir_microfone(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )
        self.clicar_e_escrever(x_escrever, y_escrever, texto, espera=espera)
        return texto

    def copiar_texto_selecionado(self) -> str:
        pyautogui.hotkey("ctrl", "c")
        self.esperar(0.5)
        return self.ler_area_transferencia()

    def clicar_e_copiar(self, x: int, y: int, espera=0.5) -> str:
        self.clicar(x, y)
        self.esperar(espera)
        return self.copiar_texto_selecionado()

    def selecionar_intervalo_e_copiar(
        self,
        x_inicial: int,
        y_inicial: int,
        x_final: int,
        y_final: int,
        espera=0.5,
    ) -> str:
        self.arrastar(x_inicial, y_inicial, x_final, y_final)
        self.esperar(espera)
        return self.copiar_texto_selecionado()

    def selecionar_tudo_e_copiar(self) -> str:
        pyautogui.hotkey("ctrl", "a")
        pyautogui.hotkey("ctrl", "c")
        self.esperar(0.5)
        return self.ler_area_transferencia()

    def tirar_print(self, arquivo="tela.png"):
        caminho = Path(arquivo)
        imagem = pyautogui.screenshot()
        imagem.save(caminho)
        return str(caminho)

    def assinatura_tela(self, largura=160, altura=90) -> str:
        imagem = pyautogui.screenshot()
        imagem = imagem.convert("L")
        imagem.thumbnail((largura, altura))
        return hashlib.md5(imagem.tobytes()).hexdigest()

    def ler_texto_da_tela(self, arquivo="tela.png") -> str:
        caminho = self.tirar_print(arquivo)
        imagem = Image.open(caminho)
        texto = pytesseract.image_to_string(imagem, lang="por")
        return texto.strip()

    def ler_area_da_tela(self, x: int, y: int, largura: int, altura: int, arquivo="area.png") -> str:
        caminho = Path(arquivo)
        imagem = pyautogui.screenshot(region=(x, y, largura, altura))
        imagem.save(caminho)
        texto = pytesseract.image_to_string(imagem, lang="por")
        return texto.strip()

    def copiar_area_da_tela(self, x: int, y: int, largura: int, altura: int, arquivo="area.png") -> str:
        return self.ler_area_da_tela(x, y, largura, altura, arquivo=arquivo)

    def aguardar_estabilidade_visual(self, timeout=20, intervalo=1, repeticoes_iguais=3) -> bool:
        inicio = time.time()
        ultima_assinatura = None
        repeticoes = 0

        while time.time() - inicio <= timeout:
            assinatura = self.assinatura_tela()

            if assinatura == ultima_assinatura:
                repeticoes += 1
            else:
                ultima_assinatura = assinatura
                repeticoes = 1

            if repeticoes >= repeticoes_iguais:
                return True

            self.esperar(intervalo)

        return False

    def aguardar_textos_na_tela(
        self,
        textos_esperados: list[str],
        timeout=20,
        intervalo=1,
        nome_base_arquivo="espera_texto",
    ) -> bool:
        inicio = time.time()
        textos_normalizados = [self._normalizar_texto(texto) for texto in textos_esperados if texto.strip()]
        tentativa = 0

        while time.time() - inicio <= timeout:
            texto_tela = self.ler_texto_da_tela(f"{nome_base_arquivo}_{tentativa:02d}.png")
            texto_normalizado = self._normalizar_texto(texto_tela)

            if all(texto in texto_normalizado for texto in textos_normalizados):
                return True

            tentativa += 1
            self.esperar(intervalo)

        return False

    def aguardar_pagina_carregar(
        self,
        timeout=20,
        intervalo=1,
        repeticoes_iguais=3,
        textos_esperados: list[str] | None = None,
        nome_base_arquivo="espera_pagina",
    ) -> bool:
        estabilizou = self.aguardar_estabilidade_visual(
            timeout=timeout,
            intervalo=intervalo,
            repeticoes_iguais=repeticoes_iguais,
        )
        if not estabilizou:
            return False

        if textos_esperados:
            return self.aguardar_textos_na_tela(
                textos_esperados=textos_esperados,
                timeout=timeout,
                intervalo=intervalo,
                nome_base_arquivo=nome_base_arquivo,
            )

        return True

    def extrair_texto_pagina(
        self,
        nome_base_arquivo="pagina",
        max_rolagens=8,
        passo_rolagem=-900,
        espera_entre_rolagens=1,
        min_chars_clipboard=80,
    ) -> str:
        texto_clipboard = self.selecionar_tudo_e_copiar().strip()
        if len(texto_clipboard) >= min_chars_clipboard:
            return texto_clipboard

        return self.extrair_texto_com_ocr_rolando(
            nome_base_arquivo=nome_base_arquivo,
            max_rolagens=max_rolagens,
            passo_rolagem=passo_rolagem,
            espera_entre_rolagens=espera_entre_rolagens,
        )

    def extrair_texto_com_ocr_rolando(
        self,
        nome_base_arquivo="pagina",
        max_rolagens=8,
        passo_rolagem=-900,
        espera_entre_rolagens=1,
    ) -> str:
        self.atalho("home")
        self.esperar(espera_entre_rolagens)

        blocos = []
        blocos_vistos = set()

        for indice in range(max_rolagens + 1):
            texto = self.ler_texto_da_tela(f"{nome_base_arquivo}_{indice:02d}.png")
            texto_limpo = self._normalizar_texto(texto)

            if texto_limpo and texto_limpo not in blocos_vistos:
                blocos.append(texto.strip())
                blocos_vistos.add(texto_limpo)

            if indice < max_rolagens:
                self.rolar(passo_rolagem)
                self.esperar(espera_entre_rolagens)

        return "\n\n".join(blocos).strip()

    def _normalizar_texto(self, texto: str) -> str:
        return " ".join(texto.split()).lower()

    def transcrever_audio_arquivo(self, caminho_audio: str) -> str:
        recognizer = sr.Recognizer()

        with sr.AudioFile(caminho_audio) as source:
            audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio, language="pt-BR")
        except sr.UnknownValueError:
            return "Nao consegui entender o audio."
        except sr.RequestError as erro:
            return f"Erro no servico de reconhecimento: {erro}"

    def ouvir_microfone(self, timeout=10, phrase_time_limit=20) -> str:
        recognizer = sr.Recognizer()

        try:
            with sr.Microphone() as source:
                print("Ajustando ruido ambiente...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                print("Fale agora...")
                audio = recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
        except AttributeError:
            return (
                "Captura de microfone indisponivel. Instale as dependencias do sistema "
                "e execute: pip install -r requirements-audio.txt"
            )

        try:
            return recognizer.recognize_google(audio, language="pt-BR")
        except sr.UnknownValueError:
            return "Nao consegui entender o que foi dito."
        except sr.RequestError as erro:
            return f"Erro no servico de reconhecimento: {erro}"


def roteiro_exemplo():
    bot = BotVisual()
    bot.abrir_site("https://www.google.com")
    bot.escrever("consulta NCM 30049099")
    bot.pressionar("enter")
    bot.esperar(3)

    texto_tela = bot.ler_texto_da_tela()
    print("\n===== TEXTO LIDO DA TELA =====")
    print(texto_tela)

    texto_area = bot.ler_area_da_tela(
        x=100,
        y=200,
        largura=900,
        altura=500,
    )
    print("\n===== TEXTO LIDO DA AREA =====")
    print(texto_area)

    with open("resultado.txt", "w", encoding="utf-8") as arquivo:
        arquivo.write(texto_tela)


if __name__ == "__main__":
    roteiro_exemplo()
