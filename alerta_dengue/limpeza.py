"""Limpeza e padronização dos dados que chegam do InfoDengue.

Os dados brutos têm dezenas de colunas com nomes em inglês ou abreviados.
Aqui ficamos só com o necessário e com nomes claros em português.
"""

from __future__ import annotations

import pandas as pd

COLUNAS_OBRIGATORIAS = {"data_iniSE", "SE", "casos"}


def padronizar(bruto: pd.DataFrame) -> pd.DataFrame:
    """Transforma a tabela da API em uma tabela limpa, com uma linha por semana.

    Colunas de saída:
        ano, semana, inicio_semana, casos_notificados, casos_estimados,
        populacao, incidencia (casos por 100 mil habitantes)
    """
    faltando = COLUNAS_OBRIGATORIAS - set(bruto.columns)
    if faltando:
        raise ValueError(f"Colunas ausentes nos dados: {sorted(faltando)}")

    # "SE" vem no formato AAAASS. Exemplo: 202407 = semana 7 de 2024.
    se = pd.to_numeric(bruto["SE"], errors="coerce")

    casos = pd.to_numeric(bruto["casos"], errors="coerce").fillna(0)

    # As semanas mais recentes sempre têm casos que ainda não foram notificados
    # (atraso de notificação). O InfoDengue estima o valor real em "casos_est".
    # Usamos essa estimativa quando ela existe; senão, ficamos com os notificados.
    if "casos_est" in bruto.columns:
        estimados = pd.to_numeric(bruto["casos_est"], errors="coerce").fillna(casos)
    else:
        estimados = casos

    if "pop" in bruto.columns:
        populacao = pd.to_numeric(bruto["pop"], errors="coerce")
    else:
        populacao = pd.Series(float("nan"), index=bruto.index)

    tabela = pd.DataFrame(
        {
            "ano": se // 100,
            "semana": se % 100,
            "inicio_semana": pd.to_datetime(bruto["data_iniSE"], errors="coerce"),
            "casos_notificados": casos.astype(int),
            "casos_estimados": estimados.round().astype(int),
            "populacao": populacao,
        }
    )

    # Remove linhas inválidas: semana fora de 1..53 ou data que não pôde ser lida.
    validas = tabela["semana"].between(1, 53) & tabela["inicio_semana"].notna()
    tabela = tabela[validas].copy()
    tabela["ano"] = tabela["ano"].astype(int)
    tabela["semana"] = tabela["semana"].astype(int)

    # A API pode repetir a mesma semana. Ficamos com a versão mais recente.
    tabela = tabela.drop_duplicates(subset=["ano", "semana"], keep="last")

    # A população muda pouco. Se faltar em alguma semana, repetimos o valor mais próximo.
    tabela = tabela.sort_values(["ano", "semana"]).reset_index(drop=True)
    tabela["populacao"] = tabela["populacao"].ffill().bfill()

    tabela["incidencia"] = (tabela["casos_estimados"] / tabela["populacao"] * 100_000).round(2)
    return tabela
