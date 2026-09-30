"""Canal endêmico pelo método dos quartis.

O canal endêmico é uma ferramenta clássica da vigilância epidemiológica.
Ele compara a semana atual com o que costuma acontecer na MESMA semana
em anos anteriores.

Para cada semana epidemiológica (1 a 53), olhamos a incidência dos anos
de referência e calculamos:
    Q1 (quartil inferior), mediana (Q2) e Q3 (quartil superior).

Com isso, a semana atual cai em uma de quatro zonas:
    abaixo de Q1         -> "sucesso"    (menos casos que o normal)
    entre Q1 e mediana   -> "seguranca"
    entre mediana e Q3   -> "alerta"
    acima de Q3          -> "epidemia"   (mais casos que em 75% dos anos)
"""

from __future__ import annotations

import pandas as pd

ZONAS = ["sucesso", "seguranca", "alerta", "epidemia"]
MINIMO_ANOS_REFERENCIA = 3


def construir_canal(dados: pd.DataFrame, anos_referencia: list[int]) -> pd.DataFrame:
    """Calcula Q1, mediana e Q3 da incidência para cada semana.

    Retorna uma tabela indexada pela semana (1..53) com as colunas
    `q1`, `mediana` e `q3`.
    """
    if len(anos_referencia) < MINIMO_ANOS_REFERENCIA:
        raise ValueError(
            f"Use pelo menos {MINIMO_ANOS_REFERENCIA} anos de referência "
            f"(recebido: {len(anos_referencia)})."
        )

    historico = dados[dados["ano"].isin(anos_referencia)]
    anos_encontrados = set(historico["ano"].unique())
    anos_faltando = set(anos_referencia) - anos_encontrados
    if anos_faltando:
        raise ValueError(f"Não há dados para os anos de referência: {sorted(anos_faltando)}")

    # Linhas = semanas, colunas = anos, valores = incidência.
    grade = historico.pivot_table(index="semana", columns="ano", values="incidencia")

    canal = pd.DataFrame(
        {
            "q1": grade.quantile(0.25, axis=1),
            "mediana": grade.quantile(0.50, axis=1),
            "q3": grade.quantile(0.75, axis=1),
        }
    )

    # Nem todo ano tem semana 53. Se ela faltar, usamos os valores da semana 52.
    canal = canal.reindex(range(1, 54)).ffill()
    canal.index.name = "semana"
    return canal.round(2)


def classificar_zona(incidencia: float, q1: float, mediana: float, q3: float) -> str:
    """Diz em qual zona do canal endêmico uma incidência se encaixa."""
    if incidencia > q3:
        return "epidemia"
    if incidencia > mediana:
        return "alerta"
    if incidencia >= q1:
        return "seguranca"
    return "sucesso"
