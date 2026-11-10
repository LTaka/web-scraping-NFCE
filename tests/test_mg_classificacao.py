import unittest

from robo_nfce.rotinas.mg import classificacao as mg

PAGINA_INICIAL = "\n".join(mg.FRAGMENTOS_PAGINA_INICIAL)


class ClassificacaoPaginaMgTests(unittest.TestCase):
    def test_resultado(self):
        self.assertEqual(mg.RESULTADO, mg.classificar_estado_pagina("Consulta Resumida - Ambiente de Produção ..."))

    def test_pagina_inicial(self):
        self.assertEqual(mg.INICIAL, mg.classificar_estado_pagina(PAGINA_INICIAL))

    def test_pagina_com_mensagem_de_erro(self):
        texto = PAGINA_INICIAL + "\n" + "Falha na validacao do captcha. " * 10
        self.assertEqual(mg.ERRO, mg.classificar_estado_pagina(texto))

    def test_desconhecido(self):
        self.assertEqual(mg.DESCONHECIDO, mg.classificar_estado_pagina("pagina em branco"))
        self.assertTrue(mg.estado_exige_reinicio(mg.DESCONHECIDO))
        self.assertFalse(mg.estado_exige_reinicio(mg.ERRO))


if __name__ == "__main__":
    unittest.main()
