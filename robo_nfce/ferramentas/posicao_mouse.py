"""Mostra a posicao do mouse a cada segundo (para calibrar coordenadas). Ctrl+C para sair."""

import time

import pyautogui


def mostrar_posicao_mouse(intervalo: float = 1.0) -> None:
    try:
        while True:
            print(pyautogui.position())
            time.sleep(intervalo)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    mostrar_posicao_mouse()
