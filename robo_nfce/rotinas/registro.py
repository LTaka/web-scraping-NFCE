from typing import TYPE_CHECKING

from robo_nfce.config import ConfigUF
from robo_nfce.rotinas.audio import RotinaBAComAudio, RotinaSPComAudio
from robo_nfce.rotinas.base import RotinaEstado
from robo_nfce.rotinas.es import RotinaESPadrao
from robo_nfce.rotinas.mg import RotinaMGPadrao
from robo_nfce.rotinas.rj import RotinaRJPadrao

if TYPE_CHECKING:
    from robo_nfce.bot.visual import BotVisual

# Nome usado em ConfigUF.rotina -> classe da rotina.
ROTINAS: dict[str, type[RotinaEstado]] = {
    "mg_padrao": RotinaMGPadrao,
    "es_padrao": RotinaESPadrao,
    "sp_com_audio": RotinaSPComAudio,
    "ba_com_audio": RotinaBAComAudio,
    "rj_padrao": RotinaRJPadrao,
}


def criar_rotina(bot: "BotVisual", config: ConfigUF, modo_execucao: str) -> RotinaEstado:
    try:
        classe_rotina = ROTINAS[config.rotina]
    except KeyError as erro:
        raise KeyError(f"Rotina {config.rotina} nao encontrada para a UF {config.uf}.") from erro
    return classe_rotina(bot, config, modo_execucao)
