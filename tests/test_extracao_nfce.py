import tempfile
import unittest
from pathlib import Path

from robo_nfce.extracao.nfce import extrair_campos_nfce
from robo_nfce.extracao.textos_capturados import atualizar_csv_existente_com_textos, gerar_csv_de_textos_capturados
from robo_nfce.utils.csv_io import ler_csv

TEXTO_MG_DIESEL = (
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


class ExtratorNfceMgTests(unittest.TestCase):
    def test_extrai_consulta_resumida_atual_sem_classificar_filtro_como_combustivel(self):
        texto = (
            "Consulta Resumida - Ambiente de Produção\n"
            "Chave de acesso\n"
            "31-23/05-33.823.779/0001-02-65-001-000.141.087-110.032.4805\n"
            "NFC-e\n"
            "Modelo Série Número Data Emissão\n"
            "65 1 141087 01/05/2023 10:39:06\n"
            "Produtos e Serviços\n"
            "Número Descrição Quantidade Unidade Comercial Valor Unitário Valor(R$)\n"
            "1 MOBIL SUPER 5W 40 5.000 Un R$ 55,60 R$ 278,00\n"
            "2 FILTRO ARL 6080 1.000 Un R$ 29,99 R$ 29,99\n"
            "3 FILTRO PSL 545 1.000 Un R$ 39,80 R$ 39,80\n"
            "4 FILTRO GASOLINA GI50/7 1.000 Un R$ 26,00 R$ 26,00\n"
            "Situação atual: AUTORIZADA\n"
        )

        campos = extrair_campos_nfce(texto)

        self.assertEqual("31230533823779000102650010001410871100324805", campos["chave"])
        self.assertEqual("141087", campos["nota_numero"])
        self.assertEqual("01/05/2023 10:39:06", campos["nota_emissao"])
        self.assertEqual("sim", campos["tem_itens"])
        self.assertEqual(4, len(campos["itens"]))
        self.assertEqual("MOBIL SUPER 5W 40", campos["itens"][0]["item_descricao"])
        self.assertEqual("5,000", campos["itens"][0]["item_qtde"])
        self.assertEqual("Un", campos["itens"][0]["item_un"])
        self.assertEqual("278,00", campos["itens"][0]["item_vl_total"])
        self.assertEqual("nao", campos["tem_combustivel"])
        self.assertEqual("", campos["combustiveis"])

    def test_extrai_itens_tabela_mg_com_quantidade_e_valor_com_milhar(self):
        campos = extrair_campos_nfce(TEXTO_MG_DIESEL)

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

    def test_texto_vazio_retorna_sem_itens(self):
        campos = extrair_campos_nfce("")
        self.assertEqual("nao", campos["tem_itens"])
        self.assertEqual([], campos["itens"])


class TextosCapturadosTests(unittest.TestCase):
    def test_gera_csv_com_uma_linha_por_item(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            (pasta / "31230533823779000102650010001415271100329377.txt").write_text(TEXTO_MG_DIESEL, encoding="utf-8")
            saida = pasta / "saida.csv"

            total = gerar_csv_de_textos_capturados(pasta, saida)

            _, linhas = ler_csv(saida)
            self.assertEqual(1, total)
            self.assertEqual("DIESEL COMUM S500", linhas[0]["item_descricao"])
            self.assertEqual("sim", linhas[0]["tem_combustivel"])

    def test_atualiza_somente_chaves_sem_itens(self):
        chave = "31230533823779000102650010001415271100329377"
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            textos = pasta / "textos"
            textos.mkdir()
            (textos / f"{chave}.txt").write_text(TEXTO_MG_DIESEL, encoding="utf-8")
            (textos / "999.txt").write_text(TEXTO_MG_DIESEL, encoding="utf-8")
            base = pasta / "base.csv"
            base.write_text(f"chave,tem_itens\n{chave},nao\n999,sim\n", encoding="utf-8")
            saida = pasta / "saida.csv"

            atualizadas = atualizar_csv_existente_com_textos(
                entrada_csv=base, saida=saida, pasta_textos=textos, somente_sem_itens=True
            )

            _, linhas = ler_csv(saida)
            self.assertEqual(1, atualizadas)
            self.assertEqual("sim", linhas[0]["tem_itens"])
            self.assertEqual("", linhas[1]["item_descricao"])


if __name__ == "__main__":
    unittest.main()
