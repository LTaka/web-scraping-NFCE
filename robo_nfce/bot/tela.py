import hashlib
import time
from pathlib import Path

import pyautogui
import pytesseract
from PIL import Image

from robo_nfce.utils.texto import normalizar_espacos

IDIOMA_OCR = "por"


class TelaMixin:
    """Screenshots, OCR e esperas baseadas no conteudo da tela."""

    def tirar_print(self, arquivo="tela.png") -> str:
        caminho = Path(arquivo)
        pyautogui.screenshot().save(caminho)
        return str(caminho)

    def assinatura_tela(self, largura=160, altura=90) -> str:
        """Hash de uma miniatura em tons de cinza: muda quando a tela muda."""
        imagem = pyautogui.screenshot().convert("L")
        imagem.thumbnail((largura, altura))
        return hashlib.md5(imagem.tobytes()).hexdigest()

    def ler_texto_da_tela(self, arquivo="tela.png") -> str:
        caminho = self.tirar_print(arquivo)
        return pytesseract.image_to_string(Image.open(caminho), lang=IDIOMA_OCR).strip()

    def ler_area_da_tela(self, x: int, y: int, largura: int, altura: int, arquivo="area.png") -> str:
        imagem = pyautogui.screenshot(region=(x, y, largura, altura))
        imagem.save(Path(arquivo))
        return pytesseract.image_to_string(imagem, lang=IDIOMA_OCR).strip()

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
        self, textos_esperados: list[str], timeout=20, intervalo=1, nome_base_arquivo="espera_texto"
    ) -> bool:
        inicio = time.time()
        esperados = [normalizar_espacos(texto) for texto in textos_esperados if texto.strip()]
        tentativa = 0

        while time.time() - inicio <= timeout:
            texto_tela = normalizar_espacos(self.ler_texto_da_tela(f"{nome_base_arquivo}_{tentativa:02d}.png"))
            if all(texto in texto_tela for texto in esperados):
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
        if not self.aguardar_estabilidade_visual(timeout, intervalo, repeticoes_iguais):
            return False
        if textos_esperados:
            return self.aguardar_textos_na_tela(textos_esperados, timeout, intervalo, nome_base_arquivo)
        return True

    def extrair_texto_pagina(
        self,
        nome_base_arquivo="pagina",
        max_rolagens=8,
        passo_rolagem=-900,
        espera_entre_rolagens=1,
        min_chars_clipboard=80,
    ) -> str:
        """Tenta Ctrl+A/Ctrl+C; se vier pouco texto, cai para OCR rolando a pagina."""
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
        self, nome_base_arquivo="pagina", max_rolagens=8, passo_rolagem=-900, espera_entre_rolagens=1
    ) -> str:
        self.atalho("home")
        self.esperar(espera_entre_rolagens)

        blocos = []
        blocos_vistos = set()
        for indice in range(max_rolagens + 1):
            texto = self.ler_texto_da_tela(f"{nome_base_arquivo}_{indice:02d}.png")
            texto_limpo = normalizar_espacos(texto)
            if texto_limpo and texto_limpo not in blocos_vistos:
                blocos.append(texto.strip())
                blocos_vistos.add(texto_limpo)

            if indice < max_rolagens:
                self.rolar(passo_rolagem)
                self.esperar(espera_entre_rolagens)

        return "\n\n".join(blocos).strip()
