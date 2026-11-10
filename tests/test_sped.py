import tempfile
import unittest
from pathlib import Path

from robo_nfce.sped.arquivos import gerar_csv_base_do_sped, selecionar_arquivos_txt_por_periodo
from robo_nfce.utils.csv_io import ler_csv

SPED = (
    "|0000|017|0|01052021|31052021|EMPRESA|\n"
    "|C100|1|0|PART|65|00|1|100|31000000000000000000650010000001001000000001|01052021|01052021|50,00|\n"
    "|C170|1|P1|GASOLINA COMUM|10|10,000|L|50,00|\n"
    "|C100|1|0|PART|65|02|1|101|31000000000000000000650010000001011000000002|01052021|01052021|10,00|\n"
    "|C100|1|0|PART|55|00|1|102|31000000000000000000550010000001021000000003|01052021|01052021|10,00|\n"
    "|C100|1|0|PART|65|00|1|100|31000000000000000000650010000001001000000001|01052021|01052021|50,00|\n"
)


class SpedTests(unittest.TestCase):
    def test_gera_csv_base_apenas_nfce_valida_e_sem_duplicadas(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada = Path(tmp) / "sped.txt"
            entrada.write_text(SPED, encoding="utf-8")
            saida = Path(tmp) / "saida.csv"

            total = gerar_csv_base_do_sped(str(entrada), saida)

            _, linhas = ler_csv(saida)
            self.assertEqual(1, total)
            self.assertEqual("100", linhas[0]["numero"])
            self.assertEqual("2021-05-01", linhas[0]["data"])
            self.assertEqual("50", linhas[0]["valor_total"])
            self.assertEqual("sim", linhas[0]["tem_combustivel"])
            self.assertEqual("10", linhas[0]["litros_total"])

    def test_seleciona_entrega_mais_antiga_por_periodo(self):
        base = "SPEDEFD_20210501_20210531_24093799000176_{tipo}_{entrega}_ABC123.txt"
        original = Path(base.format(tipo="Original", entrega="20210610120000"))
        retificadora = Path(base.format(tipo="Retificadora", entrega="20210710120000"))
        avulso = Path("outro.txt")

        selecionados = selecionar_arquivos_txt_por_periodo([retificadora, original, avulso])

        self.assertEqual(sorted([original, avulso]), selecionados)


if __name__ == "__main__":
    unittest.main()
