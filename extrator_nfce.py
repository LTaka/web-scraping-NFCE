import argparse
import csv
import re
import zipfile
from decimal import Decimal
from pathlib import Path


COMBUSTIVEIS = [
    "GASOLINA",
    "DIESEL",
    "ETANOL",
    "ALCOOL",
    "ÁLCOOL",
    "GNV",
]

CAMPOS_SAIDA = [
    "chave",
    "arquivo_texto_capturado",
    "nota_numero",
    "nota_emissao",
    "tem_itens",
    "tem_combustivel",
    "combustiveis",
    "litros_total",
    "valor_itens_combustivel",
    "item_descricao",
    "item_qtde",
    "item_un",
    "item_vl_unit",
    "item_vl_total",
]

CAMPOS_ITEM = [
    "item_descricao",
    "item_qtde",
    "item_un",
    "item_vl_unit",
    "item_vl_total",
]

CAMPOS_NFCE = [
    "nota_numero",
    "nota_emissao",
    "tem_itens",
    "tem_combustivel",
    "combustiveis",
    "litros_total",
    "valor_itens_combustivel",
]


def br_decimal(valor: str) -> Decimal:
    if not valor:
        return Decimal("0")
    return Decimal(valor.replace(".", "").replace(",", "."))


def decimal_br(valor: Decimal) -> str:
    return f"{valor:.3f}".replace(".", ",")


def dinheiro_br(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")


def normalizar_dinheiro_br(valor: str) -> str:
    if not valor:
        return ""
    return dinheiro_br(br_decimal(valor))


def extrair_campos_nfce(texto: str) -> dict:
    texto = texto or ""
    itens = _extrair_itens(texto)
    chave_acesso = _extrair_chave_acesso(texto)

    itens_combustivel = [
        item for item in itens
        if _eh_combustivel(item.get("item_descricao", ""))
    ]

    litros_total = sum(
        br_decimal(item.get("item_qtde", "0"))
        for item in itens_combustivel
        if item.get("item_un", "").upper() == "L"
    )

    valor_combustivel = sum(
        br_decimal(item.get("item_vl_total", "0"))
        for item in itens_combustivel
    )

    combustiveis = sorted({
        _limpar_descricao_combustivel(item["item_descricao"])
        for item in itens_combustivel
    })

    return {
        "chave": chave_acesso,
        "nota_numero": _extrair_primeiro(texto, [
            r"Numero:\s*([0-9.\-\/]+)",
            r"Numero\s*([0-9.\-\/]+)",
            r"N[uú]mero:\s*([0-9.\-\/]+)",
            r"N[uú]mero\s*([0-9.\-\/]+)",
            r"Modelo\s+S[ée]rie\s+N[uú]mero\s+Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+([0-9]+)\s+[0-9]{2}/[0-9]{2}/[0-9]{4}",
        ]),
        "nota_emissao": _extrair_primeiro(texto, [
            r"Emissao:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
            r"Emiss[aã]o:\s*([0-9]{2}/[0-9]{2}/[0-9]{4}[^\n\r]*)",
            r"Data\s+Emiss[aã]o\s*(?:\n|\s)+\d+\s+\d+\s+\d+\s+([0-9]{2}/[0-9]{2}/[0-9]{4}\s+[0-9:]{8})",
        ]),
        "itens": itens,
        "tem_itens": "sim" if itens else "nao",
        "tem_combustivel": "sim" if itens_combustivel else "nao",
        "combustiveis": " | ".join(combustiveis),
        "litros_total": decimal_br(litros_total) if itens_combustivel else "",
        "valor_itens_combustivel": dinheiro_br(valor_combustivel) if itens_combustivel else "",
    }


def _eh_combustivel(descricao: str) -> bool:
    descricao = descricao.upper()
    return any(nome in descricao for nome in COMBUSTIVEIS)


def _limpar_descricao_combustivel(descricao: str) -> str:
    descricao = re.sub(r"\s*Bico\s+[0-9]+", "", descricao, flags=re.IGNORECASE)
    return " ".join(descricao.split()).strip()


def _extrair_primeiro(texto: str, padroes: list[str]) -> str:
    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split()).strip()
    return ""


def _extrair_chave_acesso(texto: str) -> str:
    match = re.search(
        r"Chave\s+de\s+acesso[:\s]*([0-9.\-\/\s]+)",
        texto,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    digitos = re.sub(r"\D", "", match.group(1))
    return digitos if len(digitos) == 44 else ""


def _extrair_itens(texto: str) -> list[dict]:
    texto_normalizado = _normalizar_quebras(texto)
    itens = _extrair_itens_tabela_mg(texto_normalizado)
    if itens:
        return _deduplicar_itens(itens)

    linhas = [linha.strip() for linha in texto_normalizado.splitlines() if linha.strip()]
    itens = []

    for indice, linha in enumerate(linhas):
        if "vl. total" not in linha.lower():
            continue

        bloco = " ".join(linhas[max(0, indice - 1): min(len(linhas), indice + 2)]).strip()
        item = _parse_bloco_item(bloco)
        if item:
            itens.append(item)

    if itens:
        return _deduplicar_itens(itens)

    return _extrair_itens_texto_corrido(texto_normalizado)


def _extrair_itens_tabela_mg(texto: str) -> list[dict]:
    if "Produtos e Serviços" not in texto or "Valor(R$)" not in texto:
        return []

    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    capturando = False
    itens = []
    padrao_valor = r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}"
    padrao_qtde = r"\d+(?:[.,]\d+)*"
    padrao_item = re.compile(
        r"^\s*\d+\s+"
        r"(?P<descricao>.+?)\s+"
        rf"(?P<qtde>{padrao_qtde})\s+"
        r"(?P<un>[A-Za-z]+)\s+"
        rf"R\$\s*(?P<vl_unit>{padrao_valor})\s+"
        rf"R\$\s*(?P<vl_total>{padrao_valor})\s*$"
    )

    for linha in linhas:
        if "Número" in linha and "Valor(R$)" in linha:
            capturando = True
            continue

        if not capturando:
            continue

        if linha.startswith("Situação atual:") or linha.startswith("Versão "):
            break

        match = padrao_item.match(linha)
        if not match:
            continue

        itens.append({
            "item_numero": linha.split()[0],
            "item_descricao": " ".join(match.group("descricao").split()).strip(" -:"),
            "item_qtde": match.group("qtde").replace(".", ","),
            "item_un": match.group("un"),
            "item_vl_unit": normalizar_dinheiro_br(match.group("vl_unit")),
            "item_vl_total": normalizar_dinheiro_br(match.group("vl_total")),
        })

    return itens


def _parse_bloco_item(bloco: str) -> dict | None:
    bloco = " ".join(bloco.split())
    padrao_valor = r"([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+,[0-9]{2})"

    total_match = re.search(rf"Vl\.\s*Total\s*{padrao_valor}", bloco, flags=re.IGNORECASE)
    qtd_match = re.search(r"Qtde\.:?\s*([0-9]+(?:,[0-9]+)?)", bloco, flags=re.IGNORECASE)
    un_match = re.search(r"UN:?\s*([A-Za-z]+)", bloco, flags=re.IGNORECASE)
    unit_match = re.search(rf"Vl\.\s*Unit\.:?\s*{padrao_valor}", bloco, flags=re.IGNORECASE)

    if not total_match:
        return None

    descricao = bloco
    descricao = re.sub(r"\(C[oó]digo:.*?\)", "", descricao, flags=re.IGNORECASE)
    descricao = re.sub(r"Qtde\.:?.*$", "", descricao, flags=re.IGNORECASE).strip(" -:")

    if not descricao:
        return None

    return {
        "item_descricao": descricao.strip(),
        "item_qtde": qtd_match.group(1) if qtd_match else "",
        "item_un": un_match.group(1) if un_match else "",
        "item_vl_unit": normalizar_dinheiro_br(unit_match.group(1)) if unit_match else "",
        "item_vl_total": normalizar_dinheiro_br(total_match.group(1)),
    }


def _extrair_itens_texto_corrido(texto: str) -> list[dict]:
    padrao_valor = r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}"
    padrao_qtde = r"[0-9]+(?:[.,][0-9]+)*"
    padrao = re.compile(
        r"(?P<descricao>[A-Z0-9][A-Z0-9\s./%-]{3,}?)"
        r"(?:\s*\(C[oó]digo:.*?\))?"
        rf"\s*Qtde\.:?\s*(?P<qtde>{padrao_qtde})"
        r"\s*UN:?\s*(?P<un>[A-Za-z]+)"
        rf"\s*Vl\.\s*Unit\.:?\s*(?P<vl_unit>{padrao_valor})"
        rf"\s*Vl\.\s*Total\s*(?P<vl_total>{padrao_valor})",
        flags=re.IGNORECASE,
    )

    itens = []
    texto_corrido = " ".join(texto.split())

    for match in padrao.finditer(texto_corrido):
        itens.append({
            "item_descricao": " ".join(match.group("descricao").split()).strip(" -:"),
            "item_qtde": match.group("qtde"),
            "item_un": match.group("un"),
            "item_vl_unit": normalizar_dinheiro_br(match.group("vl_unit")),
            "item_vl_total": normalizar_dinheiro_br(match.group("vl_total")),
        })

    return _deduplicar_itens(itens)


def _deduplicar_itens(itens: list[dict]) -> list[dict]:
    vistos = set()
    resultado = []

    for item in itens:
        chave = (
            item.get("item_numero", ""),
            item.get("item_descricao", "").lower(),
            item.get("item_qtde", ""),
            item.get("item_un", "").lower(),
            item.get("item_vl_unit", ""),
            item.get("item_vl_total", ""),
        )
        if chave in vistos:
            continue

        vistos.add(chave)
        resultado.append(item)

    return resultado


def _normalizar_quebras(texto: str) -> str:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{2,}", "\n", texto)


def listar_arquivos_texto(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    return sorted(arquivo for arquivo in entrada.glob("*.txt") if arquivo.is_file())


def extrair_txts_de_zip(arquivo_zip: Path, pasta_saida: Path) -> list[Path]:
    pasta_saida.mkdir(parents=True, exist_ok=True)
    for arquivo_existente in pasta_saida.glob("*.txt"):
        if arquivo_existente.is_file():
            arquivo_existente.unlink()

    with zipfile.ZipFile(arquivo_zip) as zip_ref:
        arquivos_extraidos = []
        for info in zip_ref.infolist():
            if info.is_dir() or not info.filename.lower().endswith(".txt"):
                continue

            destino = pasta_saida / Path(info.filename).name
            with zip_ref.open(info) as origem, destino.open("wb") as saida:
                saida.write(origem.read())
            arquivos_extraidos.append(destino)

    return sorted(arquivos_extraidos)


def preparar_entrada_textos(entrada: Path, pasta_txt_filtrados: Path | None = None) -> tuple[Path, int]:
    if entrada.is_file() and entrada.suffix.lower() == ".zip":
        if pasta_txt_filtrados is None:
            pasta_txt_filtrados = entrada.with_name(f"{entrada.stem}_txt_filtrados")
        arquivos_extraidos = extrair_txts_de_zip(entrada, pasta_txt_filtrados)
        return pasta_txt_filtrados, len(arquivos_extraidos)

    arquivos = listar_arquivos_texto(entrada)
    return entrada, len(arquivos)


def limpar_txt_filtrados(pasta_txt_filtrados: Path) -> None:
    if not pasta_txt_filtrados.exists() or not pasta_txt_filtrados.is_dir():
        return

    for arquivo in pasta_txt_filtrados.glob("*.txt"):
        if arquivo.is_file():
            arquivo.unlink()

    try:
        pasta_txt_filtrados.rmdir()
    except OSError:
        pass


def carregar_textos_por_chave(entrada: Path) -> dict[str, dict]:
    textos = {}

    for arquivo in listar_arquivos_texto(entrada):
        texto = arquivo.read_text(encoding="utf-8", errors="ignore")
        campos_nfce = extrair_campos_nfce(texto)
        chave_arquivo = arquivo.stem.strip()
        chave_texto = (campos_nfce.get("chave") or "").strip()
        chave = chave_arquivo or chave_texto
        if not chave:
            continue

        if not chave_texto:
            campos_nfce["chave"] = chave

        textos[chave] = {
            "arquivo": arquivo,
            "texto": texto,
            "campos_nfce": campos_nfce,
        }

    return textos


def _montar_fieldnames_saida(fieldnames_entrada: list[str] | None = None) -> list[str]:
    fieldnames_saida = list(fieldnames_entrada or [])
    for campo in CAMPOS_SAIDA:
        if campo not in fieldnames_saida:
            fieldnames_saida.append(campo)
    return fieldnames_saida or list(CAMPOS_SAIDA)


def _aplicar_campos_nfce_na_linha(linha: dict, campos_nfce: dict, caminho_texto: Path | None) -> dict:
    linha["chave"] = campos_nfce.get("chave") or linha.get("chave", "")
    linha["arquivo_texto_capturado"] = str(caminho_texto) if caminho_texto else linha.get("arquivo_texto_capturado", "")

    for campo in CAMPOS_NFCE:
        linha[campo] = campos_nfce.get(campo, "")

    return linha


def _limpar_campos_item(linha: dict) -> dict:
    for campo in CAMPOS_ITEM:
        linha[campo] = ""
    return linha


def _expandir_resultado_saida(linha_base: dict, campos_nfce: dict) -> list[dict]:
    itens = campos_nfce["itens"]

    if not itens:
        return [_limpar_campos_item(dict(linha_base))]

    linhas_expandidas = []
    for item in itens:
        linha_item = _limpar_campos_item(dict(linha_base))
        linha_item["item_descricao"] = item.get("item_descricao", "")
        linha_item["item_qtde"] = item.get("item_qtde", "")
        linha_item["item_un"] = item.get("item_un", "")
        linha_item["item_vl_unit"] = item.get("item_vl_unit", "")
        linha_item["item_vl_total"] = item.get("item_vl_total", "")
        linhas_expandidas.append(linha_item)
    return linhas_expandidas


def gerar_csv_de_textos_capturados(entrada: Path, saida: Path, delimitador: str) -> int:
    textos_por_chave = carregar_textos_por_chave(entrada)
    fieldnames_saida = _montar_fieldnames_saida()
    linhas_saida = []

    for chave in sorted(textos_por_chave):
        dados = textos_por_chave[chave]
        campos_nfce = dados["campos_nfce"]
        linha_base = {"chave": chave}
        _aplicar_campos_nfce_na_linha(linha_base, campos_nfce, dados["arquivo"])
        linhas_saida.extend(_expandir_resultado_saida(linha_base, campos_nfce))

    with saida.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames_saida, delimiter=delimitador)
        writer.writeheader()
        writer.writerows(linhas_saida)

    return len(textos_por_chave)


def atualizar_csv_existente_com_textos(
    *,
    entrada_csv: Path,
    saida: Path,
    pasta_textos: Path,
    delimitador: str,
    somente_sem_itens: bool,
) -> int:
    textos_por_chave = carregar_textos_por_chave(pasta_textos)

    with entrada_csv.open("r", encoding="utf-8-sig", newline="") as arquivo_entrada:
        leitor = csv.DictReader(arquivo_entrada, delimiter=delimitador)
        if not leitor.fieldnames:
            raise ValueError("O CSV base precisa ter cabecalho.")

        fieldnames_saida = _montar_fieldnames_saida(leitor.fieldnames)
        linhas_entrada = list(leitor)

    grupos = {}
    ordem_chaves = []
    for linha in linhas_entrada:
        chave = (linha.get("chave") or "").strip()
        if chave not in grupos:
            grupos[chave] = []
            ordem_chaves.append(chave)
        grupos[chave].append(linha)

    linhas_saida = []
    chaves_atualizadas = 0

    for chave in ordem_chaves:
        grupo = grupos[chave]
        linha_representante = dict(grupo[0])
        texto_disponivel = textos_por_chave.get(chave)

        if not texto_disponivel:
            linhas_saida.extend(grupo)
            continue

        if somente_sem_itens and (linha_representante.get("tem_itens") or "").strip().lower() != "nao":
            linhas_saida.extend(grupo)
            continue

        campos_nfce = texto_disponivel["campos_nfce"]
        linha_atualizada = _aplicar_campos_nfce_na_linha(
            dict(linha_representante),
            campos_nfce,
            texto_disponivel["arquivo"],
        )
        linhas_saida.extend(_expandir_resultado_saida(linha_atualizada, campos_nfce))
        chaves_atualizadas += 1

    with saida.open("w", encoding="utf-8", newline="") as arquivo_saida:
        escritor = csv.DictWriter(arquivo_saida, fieldnames=fieldnames_saida, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows([
            {campo: linha.get(campo, "") for campo in fieldnames_saida}
            for linha in linhas_saida
        ])

    return chaves_atualizadas


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Le textos capturados de NFC-e e gera ou atualiza um resultado.csv.",
    )
    parser.add_argument(
        "entrada",
        help="Pasta com .txt, arquivo .txt ou arquivo .zip com os textos capturados.",
    )
    parser.add_argument(
        "--saida",
        default="resultado.csv",
        help="Caminho do CSV de saida.",
    )
    parser.add_argument(
        "--csv-base",
        default=None,
        help="CSV existente para atualizar pelas chaves dos textos capturados.",
    )
    parser.add_argument(
        "--delimitador",
        default=",",
        help="Delimitador do CSV de saida.",
    )
    parser.add_argument(
        "--pasta-txt-filtrados",
        default=None,
        help="Pasta temporaria usada para extrair .txt quando a entrada for um .zip.",
    )
    parser.add_argument(
        "--somente-sem-itens",
        action="store_true",
        help="Ao usar --csv-base, atualiza apenas linhas que hoje estao com tem_itens=nao.",
    )
    return parser


if __name__ == "__main__":
    args = criar_parser().parse_args()
    entrada_original = Path(args.entrada)
    entrada_preparada, _ = preparar_entrada_textos(
        entrada=entrada_original,
        pasta_txt_filtrados=Path(args.pasta_txt_filtrados) if args.pasta_txt_filtrados else None,
    )

    if args.csv_base:
        quantidade = atualizar_csv_existente_com_textos(
            entrada_csv=Path(args.csv_base),
            saida=Path(args.saida),
            pasta_textos=entrada_preparada,
            delimitador=args.delimitador,
            somente_sem_itens=args.somente_sem_itens,
        )
        print(f"CSV atualizado com {quantidade} chave(s): {args.saida}")
    else:
        quantidade = gerar_csv_de_textos_capturados(
            entrada=entrada_preparada,
            saida=Path(args.saida),
            delimitador=args.delimitador,
        )
        print(f"CSV gerado com {quantidade} texto(s): {args.saida}")

    if entrada_original.suffix.lower() == ".zip":
        limpar_txt_filtrados(entrada_preparada)
