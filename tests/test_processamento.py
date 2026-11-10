import csv
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from robo_nfce.processamento import lote


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


def _resposta(texto: str, observacao: str) -> dict:
    return {
        "status_robo": "ok",
        "uf": "MG",
        "url_consulta": "http://teste",
        "texto_capturado": texto,
        "texto_audio": "",
        "observacao": observacao,
    }


class RetentativaTests(unittest.TestCase):
    def setUp(self):
        self.config = SimpleNamespace(codigo_ibge="31", uf="MG", url="http://teste")

    def _executar(self, rotina, repetir_sem_itens):
        contexto = lote.ContextoLote(bot=object(), modo="executar")
        with patch.object(lote, "obter_config_por_chave", return_value=self.config), patch.object(
            lote, "criar_rotina", return_value=rotina
        ):
            return lote.executar_consulta_com_retentativa(
                chave="3123",
                linha={},
                indice=2,
                contexto=contexto,
                repetir_sem_itens=repetir_sem_itens,
                max_tentativas_sem_itens=2,
            )

    def test_nao_repete_quando_flag_desabilitada(self):
        rotina = RotinaSequencialStub([
            _resposta("Chave de acesso: 1", "primeira tentativa"),
            _resposta("Produtos e Serviços\nNúmero Valor(R$)\n1 GASOLINA 1 L R$ 5,00 R$ 5,00", "segunda"),
        ])

        resultado = self._executar(rotina, repetir_sem_itens=False)

        self.assertEqual("nao", resultado.campos_nfce["tem_itens"])
        self.assertEqual(["3123"], rotina.chaves_executadas)

    def test_repete_apenas_quando_sem_itens_e_encontra_na_segunda_tentativa(self):
        rotina = RotinaSequencialStub([
            _resposta("Consulta concluida sem itens", "primeira tentativa"),
            _resposta(
                "Produtos e Serviços\n"
                "Número Descrição Quantidade Unidade Comercial Valor Unitário Valor(R$)\n"
                "1 GASOLINA COMUM 10 L R$ 5,00 R$ 50,00",
                "segunda tentativa",
            ),
        ])

        resultado = self._executar(rotina, repetir_sem_itens=True)

        self.assertEqual("sim", resultado.campos_nfce["tem_itens"])
        self.assertEqual(["3123", "3123"], rotina.chaves_executadas)
        self.assertIn("Itens encontrados apos retentativa", resultado.linha["observacao"])

    def test_erro_na_pagina_inicial_vira_erro_fatal_do_lote(self):
        class RotinaQuebrada:
            pagina_inicializada = False

            def executar(self, chave, linha):
                raise TimeoutError("pagina nao abriu")

        contexto = lote.ContextoLote(bot=object(), modo="executar")
        with patch.object(lote, "obter_config_por_chave", return_value=self.config), patch.object(
            lote, "criar_rotina", return_value=RotinaQuebrada()
        ), self.assertLogs(lote.logger, level="ERROR"):
            resultado = lote.executar_consulta_uma_vez(chave="31", linha={}, indice=2, contexto=contexto)

        self.assertEqual("erro", resultado.linha["status_robo"])
        self.assertIn("pagina inicial da UF MG", contexto.erro_fatal)


class FiltroEntradaTests(unittest.TestCase):
    def test_monta_fieldnames_sem_colunas_operacionais_extras(self):
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
            lote.montar_fieldnames_saida(["chave"]),
        )

    def test_filtra_apenas_tem_itens_nao_e_deduplica_por_chave(self):
        leitor = csv.DictReader(StringIO(
            "chave,tem_itens,outra\n"
            "111,nao,a\n"
            "111,nao,b\n"
            "222,sim,c\n"
            "333,NAO,d\n"
        ))

        linhas = lote.carregar_linhas_entrada(leitor=leitor, coluna_chave="chave", somente_sem_itens=True)

        self.assertEqual(
            [
                (2, {"chave": "111", "tem_itens": "nao", "outra": "a"}),
                (5, {"chave": "333", "tem_itens": "NAO", "outra": "d"}),
            ],
            linhas,
        )


if __name__ == "__main__":
    unittest.main()
