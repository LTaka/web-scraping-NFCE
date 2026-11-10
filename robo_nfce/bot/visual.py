import logging
import time

import pyautogui

from robo_nfce.bot.audio import AudioMixin
from robo_nfce.bot.mouse import MouseMixin
from robo_nfce.bot.navegador import NavegadorMixin
from robo_nfce.bot.tela import TelaMixin
from robo_nfce.bot.teclado import TecladoMixin

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5


class BotVisual(MouseMixin, TecladoMixin, NavegadorMixin, TelaMixin, AudioMixin):
    """Fachada unica usada pelas rotinas estaduais."""

    def __init__(self):
        self.print_posicao_mouse()

    def print_posicao_mouse(self):
        logger.info("Mova o mouse para o canto superior esquerdo para parar o robo.")
        logger.info("Posicao atual: %s", pyautogui.position())

    def esperar(self, segundos=2):
        time.sleep(segundos)
