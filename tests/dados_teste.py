"""Gera tabelas no mesmo formato da API do InfoDengue, para usar nos testes.

Os testes não acessam a internet: assim eles são rápidos e sempre dão o
mesmo resultado.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

POPULACAO = 1_500_000


def serie_api(casos_por_ano: dict[int, list[int]], populacao: int = POPULACAO) -> pd.DataFrame:
    """Cria uma tabela "bruta" como a da API.

    `casos_por_ano` mapeia o ano para a lista de casos das semanas 1, 2, 3...
    """
    linhas = []
    for ano, casos in casos_por_ano.items():
        inicio = date(ano, 1, 1) - timedelta(days=date(ano, 1, 1).weekday() + 1)
        for indice, total in enumerate(casos):
            semana = indice + 1
            linhas.append(
                {
                    "data_iniSE": (inicio + timedelta(weeks=indice)).isoformat(),
                    "SE": ano * 100 + semana,
                    "casos_est": total,
                    "casos": total,
                    "pop": populacao,
                    "nivel": 1,
                }
            )
    return pd.DataFrame(linhas)


def ano_constante(valor: int, semanas: int = 52) -> list[int]:
    return [valor] * semanas
