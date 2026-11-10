"""Clipboard com fallback para tkinter quando o pyperclip nao tem backend."""

import tkinter as tk

import pyperclip
from pyperclip import PyperclipException


def copiar(texto: str) -> bool:
    try:
        pyperclip.copy(texto)
        return True
    except PyperclipException:
        pass

    try:
        raiz = tk.Tk()
        raiz.withdraw()
        raiz.clipboard_clear()
        raiz.clipboard_append(texto)
        raiz.update()
        raiz.destroy()
        return True
    except tk.TclError:
        return False


def ler() -> str:
    try:
        return pyperclip.paste()
    except PyperclipException:
        pass

    try:
        raiz = tk.Tk()
        raiz.withdraw()
        texto = raiz.clipboard_get()
        raiz.destroy()
        return texto
    except tk.TclError:
        return ""
