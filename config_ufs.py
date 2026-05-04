import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigUF:
    codigo_ibge: str
    uf: str
    nome: str
    url: str
    rotina: str
    usar_audio: bool = False


CONFIGS_UF = {
    "31": ConfigUF(
        codigo_ibge="31",
        uf="MG",
        nome="Minas Gerais",
        url="portalsped.fazenda.mg.gov.br/portalnfce/sistema/consultaarg.xhtml",
        rotina="mg_padrao",
    ),
    "32": ConfigUF(
        codigo_ibge="32",
        uf="ES",
        nome="Espirito Santo",
        url="app.sefaz.es.gov.br/consultaNFCe/",
        rotina="es_padrao",
    ),
    "35": ConfigUF(
        codigo_ibge="35",
        uf="SP",
        nome="Sao Paulo",
        url="www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaPublica.aspx",
        rotina="sp_com_audio",
        usar_audio=True,
    ),
    "29": ConfigUF(
        codigo_ibge="29",
        uf="BA",
        nome="Bahia",
        url="nfe.sefaz.ba.gov.br/servicos/nfce/Modulos/Geral/NFCEC_consulta_chave_acesso.aspx",
        rotina="ba_com_audio",
        usar_audio=True,
    ),
    "33": ConfigUF(
        codigo_ibge="33",
        uf="RJ",
        nome="Rio de Janeiro",
        url="www4.fazenda.rj.gov.br/consultaDFe/paginas/consultaChaveAcesso.faces",
        rotina="rj_padrao",
    ),
}


def extrair_codigo_estado(chave: str) -> str:
    digitos = "".join(re.findall(r"\d", str(chave)))
    if len(digitos) < 2:
        raise ValueError(f"Nao foi possivel extrair o codigo do estado da chave: {chave}")
    return digitos[:2]


def obter_config_por_chave(chave: str) -> ConfigUF:
    codigo = extrair_codigo_estado(chave)
    try:
        return CONFIGS_UF[codigo]
    except KeyError as erro:
        raise KeyError(f"Estado com codigo {codigo} ainda nao foi configurado.") from erro
