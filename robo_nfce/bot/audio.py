import logging

import speech_recognition as sr

logger = logging.getLogger(__name__)

IDIOMA_RECONHECIMENTO = "pt-BR"


class AudioMixin:
    """Reconhecimento de voz (Google Speech) a partir de arquivo ou microfone."""

    def transcrever_audio_arquivo(self, caminho_audio: str) -> str:
        recognizer = sr.Recognizer()
        with sr.AudioFile(caminho_audio) as source:
            audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio, language=IDIOMA_RECONHECIMENTO)
        except sr.UnknownValueError:
            return "Nao consegui entender o audio."
        except sr.RequestError as erro:
            return f"Erro no servico de reconhecimento: {erro}"

    def ouvir_microfone(self, timeout=10, phrase_time_limit=20) -> str:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                logger.info("Ajustando ruido ambiente...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Fale agora...")
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        except AttributeError:
            return (
                "Captura de microfone indisponivel. Instale as dependencias do sistema "
                "e execute: pip install -r requirements-audio.txt"
            )

        try:
            return recognizer.recognize_google(audio, language=IDIOMA_RECONHECIMENTO)
        except sr.UnknownValueError:
            return "Nao consegui entender o que foi dito."
        except sr.RequestError as erro:
            return f"Erro no servico de reconhecimento: {erro}"

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
        texto = self.ouvir_microfone(timeout=timeout, phrase_time_limit=phrase_time_limit)
        self.clicar_e_escrever(x_escrever, y_escrever, texto, espera=espera)
        return texto
