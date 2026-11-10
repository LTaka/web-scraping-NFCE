import zipfile
from pathlib import Path
from typing import Callable


def listar_arquivos_texto(entrada: Path) -> list[Path]:
    """Retorna o proprio arquivo ou todos os .txt de uma pasta (ordenados)."""
    if entrada.is_file():
        return [entrada]
    return sorted(arquivo for arquivo in entrada.glob("*.txt") if arquivo.is_file())


def _limpar_txts(pasta: Path) -> None:
    for arquivo in pasta.glob("*.txt"):
        if arquivo.is_file():
            arquivo.unlink()


def extrair_txts_de_zip(
    arquivo_zip: Path,
    pasta_saida: Path,
    filtro_nomes: Callable[[list[str]], set[str]] | None = None,
) -> list[Path]:
    """Extrai os .txt do zip para `pasta_saida` (achatando subpastas).

    `filtro_nomes` recebe todos os nomes de .txt e devolve o conjunto que deve ser extraido.
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)
    _limpar_txts(pasta_saida)

    with zipfile.ZipFile(arquivo_zip) as zip_ref:
        membros_txt = [
            info for info in zip_ref.infolist()
            if not info.is_dir() and info.filename.lower().endswith(".txt")
        ]
        nomes = [Path(info.filename).name for info in membros_txt]
        selecionados = filtro_nomes(nomes) if filtro_nomes else set(nomes)

        extraidos = []
        for info in membros_txt:
            nome = Path(info.filename).name
            if nome not in selecionados:
                continue
            destino = pasta_saida / nome
            with zip_ref.open(info) as origem, destino.open("wb") as saida:
                saida.write(origem.read())
            extraidos.append(destino)

    return sorted(extraidos)


def preparar_entrada_txt(
    entrada: Path,
    pasta_txt_filtrados: Path | None = None,
    filtro_nomes: Callable[[list[str]], set[str]] | None = None,
) -> tuple[Path, int]:
    """Se a entrada for .zip, extrai os .txt para uma pasta temporaria e retorna essa pasta."""
    if entrada.is_file() and entrada.suffix.lower() == ".zip":
        if pasta_txt_filtrados is None:
            pasta_txt_filtrados = entrada.with_name(f"{entrada.stem}_txt_filtrados")
        extraidos = extrair_txts_de_zip(entrada, pasta_txt_filtrados, filtro_nomes)
        return pasta_txt_filtrados, len(extraidos)

    return entrada, len(listar_arquivos_texto(entrada))


def limpar_txt_filtrados(pasta_txt_filtrados: Path) -> None:
    """Remove os .txt extraidos e a pasta, se ficar vazia."""
    if not pasta_txt_filtrados.is_dir():
        return
    _limpar_txts(pasta_txt_filtrados)
    try:
        pasta_txt_filtrados.rmdir()
    except OSError:
        pass
