"""Testa o reconhecimento de voz pelo microfone e, opcionalmente, de um arquivo .wav."""

import argparse
import logging

from robo_nfce.bot.visual import BotVisual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", help="Arquivo de audio (.wav) para transcrever.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    bot = BotVisual()
    print("Texto falado:", bot.ouvir_microfone())
    if args.arquivo:
        print("Texto do arquivo:", bot.transcrever_audio_arquivo(args.arquivo))


if __name__ == "__main__":
    main()
