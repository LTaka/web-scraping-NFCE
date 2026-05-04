import time

import pyautogui


def mostrar_posicao_mouse():
    while True:
        print(pyautogui.position())
        time.sleep(1)


if __name__ == "__main__":
    mostrar_posicao_mouse()
