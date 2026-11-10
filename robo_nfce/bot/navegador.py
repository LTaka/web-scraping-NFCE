import pyautogui


class NavegadorMixin:
    """Acoes na barra de endereco do navegador ja aberto e focado."""

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
