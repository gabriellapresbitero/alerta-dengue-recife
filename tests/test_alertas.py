import unittest

import pandas as pd

from alerta_dengue.alertas import avaliar_semanas, calcular_crescimento
from alerta_dengue.canal_endemico import construir_canal
from alerta_dengue.limpeza import padronizar
from tests.dados_teste import ano_constante, serie_api

HISTORICO = {
    2019: ano_constante(15),
    2020: ano_constante(30),
    2021: ano_constante(45),
    2022: ano_constante(60),
    2023: ano_constante(75),
}  # canal: Q1 = 30 casos, mediana = 45, Q3 = 60 (por semana)


def avaliar(casos_2024):
    dados = padronizar(serie_api({**HISTORICO, 2024: casos_2024}))
    canal = construir_canal(dados, list(HISTORICO))
    return avaliar_semanas(dados[dados["ano"] == 2024], canal)


class TestCrescimento(unittest.TestCase):
    def test_compara_janelas_de_tres_semanas(self):
        casos = pd.Series([10, 10, 10, 12, 12, 12])
        self.assertAlmostEqual(calcular_crescimento(casos).iloc[-1], 0.2)

    def test_primeiras_semanas_ficam_sem_valor(self):
        casos = pd.Series([10, 10, 10, 12, 12, 12])
        self.assertTrue(calcular_crescimento(casos).iloc[:5].isna().all())

    def test_periodo_anterior_zerado_nao_divide_por_zero(self):
        casos = pd.Series([0, 0, 0, 5, 5, 5])
        self.assertTrue(pd.isna(calcular_crescimento(casos).iloc[-1]))


class TestAvaliarSemanas(unittest.TestCase):
    def test_semanas_normais_ficam_verdes(self):
        resultado = avaliar(ano_constante(40, semanas=10))
        self.assertTrue((resultado["nivel"] == "verde").all())

    def test_acima_do_q3_por_duas_semanas_fica_vermelho(self):
        resultado = avaliar(ano_constante(90, semanas=10))
        self.assertEqual(resultado["nivel"].iloc[-1], "vermelho")
        self.assertIn("Q3", resultado["motivo"].iloc[-1])

    def test_primeira_semana_acima_do_q3_fica_laranja(self):
        # Evita alarme falso: uma semana isolada acima do Q3 ainda não é vermelho.
        resultado = avaliar([40, 40, 40, 40, 40, 90])
        self.assertEqual(resultado["nivel"].iloc[-1], "laranja")
        self.assertIn("continuar", resultado["motivo"].iloc[-1])

    def test_acima_da_mediana_estavel_fica_amarelo(self):
        resultado = avaliar(ano_constante(50, semanas=10))
        self.assertEqual(resultado["nivel"].iloc[-1], "amarelo")

    def test_acima_da_mediana_e_crescendo_fica_laranja(self):
        # semanas 1-3 com 40 casos, semanas 4-6 com 55: +37,5% e acima da mediana
        resultado = avaliar([40, 40, 40, 55, 55, 55])
        self.assertEqual(resultado["nivel"].iloc[-1], "laranja")

    def test_crescimento_forte_abaixo_da_mediana_fica_amarelo(self):
        resultado = avaliar([20, 20, 20, 35, 35, 35])
        ultima = resultado.iloc[-1]
        self.assertEqual(ultima["zona"], "seguranca")
        self.assertEqual(ultima["nivel"], "amarelo")
        self.assertIn("subiram", ultima["motivo"])

    def test_todo_alerta_tem_motivo(self):
        resultado = avaliar([20, 40, 60, 80, 100, 120])
        self.assertTrue(resultado["motivo"].str.len().gt(0).all())


if __name__ == "__main__":
    unittest.main()
