import sys
import types
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch


bot_visual_stub = types.ModuleType("bot_visual")


class BotVisualStub:
    pass


bot_visual_stub.BotVisual = BotVisualStub
sys.modules.setdefault("bot_visual", bot_visual_stub)

rotinas_stub = types.ModuleType("rotinas_estaduais")
rotinas_stub.criar_rotina = lambda bot, config, modo: None
sys.modules.setdefault("rotinas_estaduais", rotinas_stub)

import processar_csv
from extrator_nfce import extrair_campos_nfce


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


class ExtratorNfceMgTests(unittest.TestCase):
    def test_extrai_itens_tabela_mg_com_quantidade_e_valor_com_milhar(self):
        texto = (
            "Consulta Resumida - Ambiente de Produção\n"
            "Chave de acesso\n"
            "31-23/05-33.823.779/0001-02-65-001-000.141.527-110.032.9377\n"
            "NFC-e\n"
            "Modelo Série Número Data Emissão\n"
            "65 1 141527 05/05/2023 08:22:58\n"
            "Produtos e Serviços\n"
            "Número Descrição Quantidade Unidade Comercial Valor Unitário Valor(R$)\n"
            "1 DIESEL COMUM S500 245.791 L R$ 5,49 R$ 1.349,39\n"
            "Situação atual: AUTORIZADA\n"
        )

        campos = extrair_campos_nfce(texto)

        self.assertEqual("31230533823779000102650010001415271100329377", campos["chave"])
        self.assertEqual("sim", campos["tem_itens"])
        self.assertEqual("sim", campos["tem_combustivel"])
        self.assertEqual("DIESEL COMUM S500", campos["itens"][0]["item_descricao"])
        self.assertEqual("245,791", campos["itens"][0]["item_qtde"])
        self.assertEqual("1349,39", campos["itens"][0]["item_vl_total"])
        self.assertEqual("245,791", campos["litros_total"])
        self.assertEqual("1349,39", campos["valor_itens_combustivel"])

    def test_extrai_multiplos_itens_iguais_sem_perder_quantidade_formatada(self):
        texto = (
            "Produtos e Serviços\n"
            "Número Descrição Quantidade Unidade Comercial Valor Unitário Valor(R$)\n"
            "1 DIESEL S10 500.000 L R$ 5,59 R$ 2.795,00\n"
            "2 DIESEL S10 500.000 L R$ 5,59 R$ 2.795,00\n"
            "Situação atual: AUTORIZADA\n"
        )

        campos = extrair_campos_nfce(texto)

        self.assertEqual("sim", campos["tem_itens"])
        self.assertEqual(2, len(campos["itens"]))
        self.assertEqual("500,000", campos["itens"][0]["item_qtde"])
        self.assertEqual("2795,00", campos["itens"][0]["item_vl_total"])
        self.assertEqual("1000,000", campos["litros_total"])
        self.assertEqual("5590,00", campos["valor_itens_combustivel"])


class ProcessarCsvFiltroEntradaTests(unittest.TestCase):
    def test_monta_fieldnames_sem_colunas_operacionais_extras(self):
        fieldnames = processar_csv._montar_fieldnames_saida(["chave"])

        self.assertEqual(
            [
                "chave",
                "uf",
                "arquivo_texto_capturado",
                "nota_numero",
                "nota_emissao",
                "item_descricao",
                "item_qtde",
                "item_un",
                "item_vl_unit",
                "item_vl_total",
            ],
            fieldnames,
        )

    def test_filtra_apenas_tem_itens_nao_e_deduplica_por_chave(self):
        conteudo = StringIO(
            "chave,tem_itens,outra\n"
            "111,nao,a\n"
            "111,nao,b\n"
            "222,sim,c\n"
            "333,NAO,d\n"
        )
        leitor = processar_csv.csv.DictReader(conteudo, delimiter=",")

        linhas = processar_csv._carregar_linhas_entrada(
            leitor=leitor,
            primeira_coluna="chave",
            somente_sem_itens=True,
        )

        self.assertEqual(
            [
                (2, {"chave": "111", "tem_itens": "nao", "outra": "a"}),
                (5, {"chave": "333", "tem_itens": "NAO", "outra": "d"}),
            ],
            linhas,
        )


if __name__ == "__main__":
    unittest.main()
