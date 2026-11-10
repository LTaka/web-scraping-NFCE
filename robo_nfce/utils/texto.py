import re


def normalizar_espacos(texto: str | None) -> str:
    """Colapsa espacos/quebras de linha e converte para minusculas."""
    return " ".join((texto or "").split()).lower()


def normalizar_quebras(texto: str) -> str:
    """Converte quebras para '\\n' e remove linhas em branco repetidas."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{2,}", "\n", texto)


def mesclar_observacoes(observacao_atual: str, complemento: str) -> str:
    observacao_atual = (observacao_atual or "").strip()
    complemento = complemento.strip()
    if not observacao_atual:
        return complemento
    if complemento in observacao_atual:
        return observacao_atual
    return f"{observacao_atual} {complemento}"
