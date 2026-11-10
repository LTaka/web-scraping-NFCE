import pyautogui

from robo_nfce.bot import area_transferencia


class TecladoMixin:
    """Teclado, colagem e copia. Espera `esperar`, `clicar`, `arrastar` e `mover_e_clicar_em_area`."""

    def pressionar(self, tecla: str):
        pyautogui.press(tecla)

    def atalho(self, *teclas: str):
        pyautogui.hotkey(*teclas)

    def copiar_para_area_transferencia(self, texto: str) -> bool:
        return area_transferencia.copiar(texto)

    def ler_area_transferencia(self) -> str:
        return area_transferencia.ler()

    def escrever(self, texto: str):
        """Cola via clipboard; se indisponivel, digita caractere a caractere."""
        if self.copiar_para_area_transferencia(texto):
            pyautogui.hotkey("ctrl", "v")
        else:
            pyautogui.write(texto, interval=0.02)

    def colar_texto(self, texto: str):
        """Como `escrever`, mas falha se nao conseguir usar o clipboard."""
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
        self, x_min: int, x_max: int, y_min: int, y_max: int, texto: str, espera=0.5
    ) -> tuple[int, int]:
        x, y = self.mover_e_clicar_em_area(x_min, x_max, y_min, y_max, espera=espera)
        self.atalho("ctrl", "a")
        self.escrever(texto)
        return x, y

    def copiar_texto_selecionado(self) -> str:
        pyautogui.hotkey("ctrl", "c")
        self.esperar(0.5)
        return self.ler_area_transferencia()

    def clicar_e_copiar(self, x: int, y: int, espera=0.5) -> str:
        self.clicar(x, y)
        self.esperar(espera)
        return self.copiar_texto_selecionado()

    def selecionar_intervalo_e_copiar(
        self, x_inicial: int, y_inicial: int, x_final: int, y_final: int, espera=0.5
    ) -> str:
        self.arrastar(x_inicial, y_inicial, x_final, y_final)
        self.esperar(espera)
        return self.copiar_texto_selecionado()

    def selecionar_tudo_e_copiar(self) -> str:
        pyautogui.hotkey("ctrl", "a")
        pyautogui.hotkey("ctrl", "c")
        self.esperar(0.5)
        return self.ler_area_transferencia()
