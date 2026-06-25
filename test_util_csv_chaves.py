import csv
import tempfile
import unittest
from pathlib import Path

import util_csv_chaves


class UtilCsvChavesTests(unittest.TestCase):
    def test_filtra_linhas_com_ambos_os_campos_nao(self):
        linhas = [
            {"chave": "1", "tem_itens": "nao", "tem_combustivel": "nao"},
            {"chave": "2", "tem_itens": "sim", "tem_combustivel": "nao"},
            {"chave": "3", "tem_itens": "NAO", "tem_combustivel": "NAO"},
            {"chave": "4", "tem_itens": "", "tem_combustivel": "nao"},
        ]

        filtradas = util_csv_chaves.filtrar_linhas_sem_itens_e_sem_combustivel(linhas)

        self.assertEqual(["1", "3"], [linha["chave"] for linha in filtradas])

    def test_divide_lista_ao_meio_com_primeira_metade_maior_quando_impar(self):
        linhas_1, linhas_2 = util_csv_chaves.dividir_lista_ao_meio(
            [{"chave": "1"}, {"chave": "2"}, {"chave": "3"}]
        )

        self.assertEqual(["1", "2"], [linha["chave"] for linha in linhas_1])
        self.assertEqual(["3"], [linha["chave"] for linha in linhas_2])

    def test_dividir_csv_filtrado_gera_entrada_1_e_entrada_2(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pasta = Path(tmp_dir)
            entrada = pasta / "entrada.csv"
            saida_1 = pasta / "entrada_1.csv"
            saida_2 = pasta / "entrada_2.csv"

            entrada.write_text(
                (
                    "chave,tem_itens,tem_combustivel,observacao\n"
                    "1,nao,nao,a\n"
                    "2,sim,nao,b\n"
                    "3,nao,nao,c\n"
                    "4,nao,nao,d\n"
                ),
                encoding="utf-8",
            )

            total, total_1, total_2 = util_csv_chaves.dividir_csv_filtrado(entrada, saida_1, saida_2)

            self.assertEqual((3, 2, 1), (total, total_1, total_2))
            self.assertEqual(["1", "3"], self._ler_chaves(saida_1))
            self.assertEqual(["4"], self._ler_chaves(saida_2))

    def test_comparar_chaves_csv_marca_faltantes_dos_dois_lados(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pasta = Path(tmp_dir)
            arquivo_1 = pasta / "arquivo_1.csv"
            arquivo_2 = pasta / "arquivo_2.csv"
            saida = pasta / "comparacao.csv"

            arquivo_1.write_text("chave\n1\n2\n2\n4\n", encoding="utf-8")
            arquivo_2.write_text("chave\n2\n3\n4\n", encoding="utf-8")

            resumo = util_csv_chaves.comparar_chaves_csv(arquivo_1, arquivo_2, saida)

            self.assertEqual(
                {
                    "arquivo_1": 3,
                    "arquivo_2": 3,
                    "presentes_nos_dois": 2,
                    "faltando_no_arquivo_1": 1,
                    "faltando_no_arquivo_2": 1,
                },
                resumo,
            )

            with saida.open("r", encoding="utf-8", newline="") as arquivo_saida:
                linhas = list(csv.DictReader(arquivo_saida))

            self.assertEqual(
                [
                    {
                        "chave": "1",
                        "status_comparacao": "faltando_no_arquivo_2",
                        "presente_arquivo_1": "sim",
                        "presente_arquivo_2": "nao",
                    },
                    {
                        "chave": "2",
                        "status_comparacao": "presente_nos_dois",
                        "presente_arquivo_1": "sim",
                        "presente_arquivo_2": "sim",
                    },
                    {
                        "chave": "3",
                        "status_comparacao": "faltando_no_arquivo_1",
                        "presente_arquivo_1": "nao",
                        "presente_arquivo_2": "sim",
                    },
                    {
                        "chave": "4",
                        "status_comparacao": "presente_nos_dois",
                        "presente_arquivo_1": "sim",
                        "presente_arquivo_2": "sim",
                    },
                ],
                linhas,
            )

    def test_gerar_analise_faltantes_da_base_mantem_linhas_completas_da_base(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pasta = Path(tmp_dir)
            base = pasta / "base.csv"
            conferido = pasta / "conferido.csv"
            saida = pasta / "analise.csv"

            base.write_text(
                "chave,numero,observacao\n1,100,a\n2,200,b\n2,200,c\n4,400,d\n",
                encoding="utf-8",
            )
            conferido.write_text("chave\n2\n", encoding="utf-8")

            resumo = util_csv_chaves.gerar_analise_faltantes_da_base(base, conferido, saida)

            self.assertEqual(
                {
                    "base": 3,
                    "conferido": 1,
                    "faltando_no_conferido": 2,
                },
                resumo,
            )

            with saida.open("r", encoding="utf-8", newline="") as arquivo_saida:
                linhas = list(csv.DictReader(arquivo_saida))

            self.assertEqual(
                [
                    {
                        "chave": "1",
                        "numero": "100",
                        "observacao": "a",
                    },
                    {
                        "chave": "4",
                        "numero": "400",
                        "observacao": "d",
                    },
                ],
                linhas,
            )

    def _ler_chaves(self, caminho: Path) -> list[str]:
        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            return [linha["chave"] for linha in csv.DictReader(arquivo)]


if __name__ == "__main__":
    unittest.main()
