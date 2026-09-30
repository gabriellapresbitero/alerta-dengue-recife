import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alerta_dengue import banco
from alerta_dengue.__main__ import ler_argumentos, main
from tests.dados_teste import ano_constante, serie_api

DADOS_FALSOS = serie_api({
    2019: ano_constante(15),
    2020: ano_constante(30),
    2021: ano_constante(45),
    2022: ano_constante(60),
    2023: ano_constante(75),
    2024: [40, 40, 40, 55, 90, 90],
})


class TestPipelineCompleto(unittest.TestCase):
    """Roda o pipeline inteiro, trocando a API por dados falsos."""

    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.patch = mock.patch("alerta_dengue.coleta.baixar_serie", return_value=DADOS_FALSOS)
        self.baixar = self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def rodar(self, *extras):
        args = ["--municipio", "recife", "--ano", "2024", "--saida", str(self.pasta), *extras]
        with contextlib.redirect_stdout(io.StringIO()):  # esconde as mensagens de progresso
            return main(args)

    def test_gera_todos_os_arquivos(self):
        self.assertEqual(self.rodar(), 0)
        pasta = self.pasta / "2611606_2024"
        for nome in ["relatorio.md", "canal_endemico.png", "canal_endemico.csv",
                     "semanas_para_powerbi.csv"]:
            with self.subTest(arquivo=nome):
                self.assertTrue((pasta / nome).exists())

    def test_grava_no_banco_e_permite_consultar_com_sql(self):
        self.rodar()
        resultado = banco.consultar(
            self.pasta / "dengue.db",
            "SELECT semana, nivel FROM semanas WHERE ano = ? ORDER BY semana",
            (2024,),
        )
        self.assertEqual(len(resultado), 6)
        self.assertEqual(resultado["nivel"].iloc[-1], "vermelho")

    def test_rodar_duas_vezes_nao_duplica_linhas(self):
        self.rodar()
        self.rodar()
        total = banco.consultar(self.pasta / "dengue.db", "SELECT COUNT(*) AS n FROM semanas")
        self.assertEqual(total["n"].iloc[0], 6)

    def test_relatorio_mostra_situacao_atual(self):
        self.rodar()
        texto = (self.pasta / "2611606_2024" / "relatorio.md").read_text(encoding="utf-8")
        self.assertIn("semana 6/2024", texto)
        self.assertIn("VERMELHO", texto)

    def test_excluir_ano_epidemico_busca_um_ano_a_mais(self):
        self.rodar("--anos-referencia", "4", "--excluir-anos", "2023")
        _, ano_inicio, ano_fim = self.baixar.call_args.args
        self.assertEqual((ano_inicio, ano_fim), (2019, 2024))

    def test_consultas_de_exemplo_rodam_sem_erro(self):
        self.rodar()
        sql = (Path(__file__).parent.parent / "sql" / "consultas.sql").read_text(encoding="utf-8")
        consultas = [trecho for trecho in sql.split(";") if "SELECT" in trecho]
        self.assertEqual(len(consultas), 5)
        for consulta in consultas:
            with self.subTest(consulta=consulta.strip()[:60]):
                banco.consultar(self.pasta / "dengue.db", consulta)

    def test_municipio_invalido_retorna_erro(self):
        self.assertEqual(main(["--municipio", "gotham"]), 1)

    def test_argumentos_padrao(self):
        args = ler_argumentos([])
        self.assertEqual(args.municipio, "recife")
        self.assertEqual(args.anos_referencia, 5)


if __name__ == "__main__":
    unittest.main()
