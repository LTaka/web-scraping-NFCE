from bot_visual import BotVisual


def roteiro_exemplo():
    bot = BotVisual()

    texto_audio = bot.ouvir_microfone()
    print("Texto falado:", texto_audio)

    texto_arquivo = bot.transcrever_audio_arquivo("audio.wav")
    print("Texto do arquivo:", texto_arquivo)


if __name__ == "__main__":
    roteiro_exemplo()
