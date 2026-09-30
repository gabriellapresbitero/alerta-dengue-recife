import unittest

from alerta_dengue.canal_endemico import classificar_zona, construir_canal
from alerta_dengue.limpeza import padronizar
from tests.dados_teste import ano_constante, serie_api


def dados_historicos():
    # Cinco anos com casos constantes: 15, 30, 45, 60 e 75 por semana.
    # Com 1,5 milhão de habitantes, isso dá incidência de 1, 2, 3, 4 e 5.
    return padronizar(serie_api({
        2019: ano_constante(15),
        2020: ano_constante(30),
        2021: ano_constante(45),
        2022: ano_constante(60),
        2023: ano_constante(75),
    }))


class TestConstruirCanal(unittest.TestCase):
    def test_calcula_quartis_por_semana(self):
        canal = construir_canal(dados_historicos(), [2019, 2020, 2021, 2022, 2023])
        semana_10 = canal.loc[10]
        self.assertAlmostEqual(semana_10["q1"], 2.0)
        self.assertAlmostEqual(semana_10["mediana"], 3.0)
        self.assertAlmostEqual(semana_10["q3"], 4.0)

    def test_tem_todas_as_semanas_de_1_a_53(self):
        canal = construir_canal(dados_historicos(), [2019, 2020, 2021])
        self.assertEqual(list(canal.index), list(range(1, 54)))

    def test_semana_53_usa_valores_da_52(self):
        canal = construir_canal(dados_historicos(), [2019, 2020, 2021])
        self.assertEqual(canal.loc[53].tolist(), canal.loc[52].tolist())

    def test_exige_pelo_menos_tres_anos(self):
        with self.assertRaisesRegex(ValueError, "pelo menos 3"):
            construir_canal(dados_historicos(), [2022, 2023])

    def test_avisa_quando_ano_de_referencia_nao_tem_dados(self):
        with self.assertRaisesRegex(ValueError, "2010"):
            construir_canal(dados_historicos(), [2010, 2022, 2023])


class TestClassificarZona(unittest.TestCase):
    def test_zonas(self):
        casos = {
            0.5: "sucesso",
            1.0: "seguranca",  # igual ao Q1 ainda é segurança
            2.5: "alerta",
            3.0: "alerta",  # igual ao Q3 ainda é alerta
            3.1: "epidemia",
        }
        for incidencia, esperado in casos.items():
            with self.subTest(incidencia=incidencia):
                self.assertEqual(classificar_zona(incidencia, q1=1, mediana=2, q3=3), esperado)

    def test_historico_zerado_nao_gera_epidemia_com_zero_casos(self):
        self.assertEqual(classificar_zona(0, 0, 0, 0), "seguranca")


if __name__ == "__main__":
    unittest.main()
