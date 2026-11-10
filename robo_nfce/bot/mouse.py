import math
import random

import pyautogui


class MouseMixin:
    """Movimentos e cliques. Espera que a classe final defina `esperar`."""

    def clicar(self, x: int, y: int, clicks=1, intervalo=0.25):
        pyautogui.click(x, y, clicks=clicks, interval=intervalo)

    def mover_mouse_humano(self, x: int, y: int, duracao_min=0.4, duracao_max=1.2):
        """Move em curva suave com pequenos desvios aleatorios, simulando um humano."""
        posicao_atual = pyautogui.position()
        x_atual, y_atual = posicao_atual.x, posicao_atual.y
        distancia = math.hypot(x - x_atual, y - y_atual)
        duracao_total = max(random.uniform(duracao_min, duracao_max), min(2.0, distancia / 900))
        passos = max(4, min(10, int(distancia / 250) + 3))

        for passo in range(1, passos + 1):
            progresso = passo / passos
            curva = 3 * (progresso ** 2) - 2 * (progresso ** 3)
            if passo == passos:
                destino_x, destino_y = x, y
            else:
                destino_x = x_atual + (x - x_atual) * curva + random.uniform(-6, 6) * (1 - progresso)
                destino_y = y_atual + (y - y_atual) * curva + random.uniform(-6, 6) * (1 - progresso)

            duracao_passo = duracao_total / passos * random.uniform(0.75, 1.35)
            pyautogui.moveTo(destino_x, destino_y, duration=duracao_passo, tween=pyautogui.linear)

    def focar_pagina(self, proporcao_x=0.5, proporcao_y=0.45, espera=0.3):
        largura, altura = pyautogui.size()
        x = int(largura * proporcao_x)
        y = int(altura * proporcao_y)
        self.mover_mouse_humano(x, y)
        self.esperar(espera)
        self.clicar(x, y)

    def ponto_aleatorio(self, x_min: int, x_max: int, y_min: int, y_max: int) -> tuple[int, int]:
        return random.randint(x_min, x_max), random.randint(y_min, y_max)

    def escalar_ponto(self, x: int, y: int, largura_base: int, altura_base: int) -> tuple[int, int]:
        largura_atual, altura_atual = pyautogui.size()
        return int(x * largura_atual / largura_base), int(y * altura_atual / altura_base)

    def escalar_area(
        self, x_min: int, x_max: int, y_min: int, y_max: int, largura_base: int, altura_base: int
    ) -> tuple[int, int, int, int]:
        x1, y1 = self.escalar_ponto(x_min, y_min, largura_base, altura_base)
        x2, y2 = self.escalar_ponto(x_max, y_max, largura_base, altura_base)
        return x1, x2, y1, y2

    def ponto_aleatorio_escalado(
        self, x_min: int, x_max: int, y_min: int, y_max: int, largura_base: int, altura_base: int
    ) -> tuple[int, int]:
        return self.ponto_aleatorio(*self.escalar_area(x_min, x_max, y_min, y_max, largura_base, altura_base))

    def mover_e_clicar_em_area(
        self, x_min: int, x_max: int, y_min: int, y_max: int, clicks=1, intervalo=0.25, espera=0.3
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
