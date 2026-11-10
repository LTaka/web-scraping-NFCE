from robo_nfce.rotinas.base import RotinaEstado


class RotinaSPComAudio(RotinaEstado):
    """Modelo de rotina com captcha de audio (ainda nao calibrada).

    Fluxo esperado:
      1. clicar no ponto que toca o audio
      2. escutar o microfone
      3. escrever o texto ouvido no campo do captcha
      4. clicar em consultar
      5. copiar o conteudo da tela

    Exemplo com coordenadas:
        texto_audio = self.bot.clicar_ouvir_e_escrever(x_clicar=760, y_clicar=410, x_escrever=545, y_escrever=412)
        self.bot.clicar(820, 510)
        texto_tela = self.bot.copiar_area_da_tela(220, 180, 1100, 700, "captura_sp.png")
    """

    NOME_CAPTURA = "captura_sp"

    def _executar_passos(self, chave: str, linha: dict) -> dict:
        self.bot.esperar(2)
        texto_audio = self.bot.ouvir_microfone()
        texto_tela = self.bot.extrair_texto_pagina(self.NOME_CAPTURA)

        return self._resultado(
            texto_capturado=texto_tela,
            texto_audio=texto_audio,
            observacao=f"Ajuste as coordenadas da rotina {self.config.uf} com audio em robo_nfce/rotinas/audio.py.",
        )


class RotinaBAComAudio(RotinaSPComAudio):
    NOME_CAPTURA = "captura_ba"
