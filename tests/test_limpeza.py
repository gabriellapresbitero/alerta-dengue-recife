import unittest

import pandas as pd

from alerta_dengue.limpeza import padronizar
from tests.dados_teste import POPULACAO, serie_api


class TestPadronizar(unittest.TestCase):
    def test_separa_ano_e_semana_do_codigo_se(self):
        tabela = padronizar(serie_api({2024: [10, 20, 30]}))
        self.assertEqual(tabela["ano"].tolist(), [2024, 2024, 2024])
        self.assertEqual(tabela["semana"].tolist(), [1, 2, 3])

    def test_calcula_incidencia_por_100_mil(self):
        tabela = padronizar(serie_api({2024: [150]}))
        # 150 casos em 1,5 milhão de habitantes = 10 por 100 mil
        self.assertAlmostEqual(tabela.loc[0, "incidencia"], 150 / POPULACAO * 100_000)

    def test_usa_casos_estimados_quando_existem(self):
        bruto = serie_api({2024: [10]})
        bruto.loc[0, "casos"] = 4  # notificados ainda incompletos
        tabela = padronizar(bruto)
        self.assertEqual(tabela.loc[0, "casos_notificados"], 4)
        self.assertEqual(tabela.loc[0, "casos_estimados"], 10)

    def test_sem_coluna_de_estimativa_usa_notificados(self):
        bruto = serie_api({2024: [7]}).drop(columns="casos_est")
        self.assertEqual(padronizar(bruto).loc[0, "casos_estimados"], 7)

    def test_remove_semanas_duplicadas_mantendo_a_ultima(self):
        bruto = serie_api({2024: [10, 20]})
        repetida = bruto.iloc[[1]].assign(casos_est=99, casos=99)
        tabela = padronizar(pd.concat([bruto, repetida]))
        self.assertEqual(len(tabela), 2)
        self.assertEqual(tabela.loc[1, "casos_estimados"], 99)

    def test_descarta_semanas_invalidas(self):
        bruto = serie_api({2024: [10, 20]})
        bruto.loc[1, "SE"] = 202460  # semana 60 não existe
        self.assertEqual(len(padronizar(bruto)), 1)

    def test_ordena_por_ano_e_semana(self):
        bruto = serie_api({2023: [1, 2], 2024: [3, 4]}).iloc[::-1]
        tabela = padronizar(bruto)
        self.assertEqual(list(zip(tabela["ano"], tabela["semana"])),
                         [(2023, 1), (2023, 2), (2024, 1), (2024, 2)])

    def test_preenche_populacao_faltante(self):
        bruto = serie_api({2024: [10, 20]})
        bruto.loc[1, "pop"] = None
        self.assertEqual(padronizar(bruto).loc[1, "populacao"], POPULACAO)

    def test_erro_claro_quando_falta_coluna(self):
        bruto = serie_api({2024: [10]}).drop(columns="SE")
        with self.assertRaisesRegex(ValueError, "SE"):
            padronizar(bruto)


if __name__ == "__main__":
    unittest.main()
