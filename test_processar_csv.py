import sys
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch


bot_visual_stub = types.ModuleType("bot_visual")


class BotVisualStub:
    pass


bot_visual_stub.BotVisual = BotVisualStub
sys.modules.setdefault("bot_visual", bot_visual_stub)

rotinas_stub = types.ModuleType("rotinas_estaduais_2")
rotinas_stub.criar_rotina = lambda bot, config, modo: None
sys.modules.setdefault("rotinas_estaduais_2", rotinas_stub)

import processar_csv


class RotinaSequencialStub:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.pagina_inicializada = True
        self.chaves_executadas = []

    def executar(self, chave, linha):
        self.chaves_executadas.append(chave)
        if not self.respostas:
            raise AssertionError("Stub sem resposta configurada.")
        return self.respostas.pop(0)


class ProcessarCsvRetryTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(codigo_ibge="31", uf="MG", url="http://teste")

    def _criar_contexto(self, rotina):
        return {
            "bot": object(),
            "modo": "executar",
            "config_arquivo": None,
            "rotina_arquivo": None,
            "erro_fatal_lote": None,
        }

    def test_nao_repete_quando_flag_desabilitada(self):
        rotina = RotinaSequencialStub([
            {
                "status_robo": "ok",
                "uf": "MG",
                "url_consulta": "http://teste",
                "texto_capturado": "Chave de acesso: 1",
                "texto_audio": "",
                "observacao": "primeira tentativa",
            },
            {
                "status_robo": "ok",
                "uf": "MG",
                "url_consulta": "http://teste",
                "texto_capturado": "Produtos e Serviços\nNúmero Valor(R$)\n1 GASOLINA 1 L R$ 5,00 R$ 5,00",
                "texto_audio": "",
                "observacao": "segunda tentativa",
            },
        ])
        contexto = self._criar_contexto(rotina)

        with patch.object(processar_csv, "obter_config_por_chave", return_value=self.config), patch.object(
            processar_csv,
            "criar_rotina",
            return_value=rotina,
        ):
            resultado = processar_csv._executar_consulta_com_retentativa(
                chave="3123",
                linha={},
                indice=2,
                contexto=contexto,
                repetir_sem_itens=False,
                max_tentativas_sem_itens=2,
            )

        self.assertEqual("nao", resultado.campos_nfce["tem_itens"])
        self.assertEqual(["3123"], rotina.chaves_executadas)

    def test_repete_apenas_quando_sem_itens_e_encontra_na_segunda_tentativa(self):
        rotina = RotinaSequencialStub([
            {
                "status_robo": "ok",
                "uf": "MG",
                "url_consulta": "http://teste",
                "texto_capturado": "Consulta concluida sem itens",
                "texto_audio": "",
                "observacao": "primeira tentativa",
            },
            {
                "status_robo": "ok",
                "uf": "MG",
                "url_consulta": "http://teste",
                "texto_capturado": (
                    "Produtos e Serviços\n"
                    "Número Descrição Quantidade Unidade Comercial Valor Unitário Valor(R$)\n"
                    "1 GASOLINA COMUM 10 L R$ 5,00 R$ 50,00"
                ),
                "texto_audio": "",
                "observacao": "segunda tentativa",
            },
        ])
        contexto = self._criar_contexto(rotina)

        with patch.object(processar_csv, "obter_config_por_chave", return_value=self.config), patch.object(
            processar_csv,
            "criar_rotina",
            return_value=rotina,
        ):
            resultado = processar_csv._executar_consulta_com_retentativa(
                chave="3123",
                linha={},
                indice=2,
                contexto=contexto,
                repetir_sem_itens=True,
                max_tentativas_sem_itens=2,
            )

        self.assertEqual("sim", resultado.campos_nfce["tem_itens"])
        self.assertEqual(["3123", "3123"], rotina.chaves_executadas)
        self.assertIn("Itens encontrados apos retentativa", resultado.linha["observacao"])


if __name__ == "__main__":
    unittest.main()
