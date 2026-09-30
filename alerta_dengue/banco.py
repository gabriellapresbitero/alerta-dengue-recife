"""Armazenamento dos resultados em um banco SQLite.

O banco permite consultar o histórico com SQL e conectar ferramentas como
o Power BI (via ODBC) ou o DB Browser for SQLite.
Veja exemplos de consultas em `sql/consultas.sql`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

CRIAR_TABELA = """
CREATE TABLE IF NOT EXISTS semanas (
    geocodigo          INTEGER NOT NULL,
    ano                INTEGER NOT NULL,
    semana             INTEGER NOT NULL CHECK (semana BETWEEN 1 AND 53),
    inicio_semana      TEXT    NOT NULL,
    casos_notificados  INTEGER NOT NULL,
    casos_estimados    INTEGER NOT NULL,
    populacao          INTEGER,
    incidencia         REAL,
    q1                 REAL,
    mediana            REAL,
    q3                 REAL,
    zona               TEXT,
    crescimento        REAL,
    nivel              TEXT CHECK (nivel IN ('verde', 'amarelo', 'laranja', 'vermelho')),
    motivo             TEXT,
    PRIMARY KEY (geocodigo, ano, semana)
);
"""

COLUNAS = [
    "geocodigo", "ano", "semana", "inicio_semana", "casos_notificados",
    "casos_estimados", "populacao", "incidencia", "q1", "mediana", "q3",
    "zona", "crescimento", "nivel", "motivo",
]


def salvar(resultado: pd.DataFrame, geocodigo: int, caminho_banco: Path) -> int:
    """Grava (ou atualiza) as semanas avaliadas. Retorna quantas linhas foram gravadas.

    Usamos "INSERT ... ON CONFLICT DO UPDATE" (upsert): se a semana já existe
    no banco, os valores são atualizados. Isso é importante porque os números
    das semanas recentes mudam conforme chegam novas notificações.
    """
    tabela = resultado.copy()
    tabela["geocodigo"] = geocodigo
    tabela["inicio_semana"] = pd.to_datetime(tabela["inicio_semana"]).dt.strftime("%Y-%m-%d")
    tabela["populacao"] = tabela["populacao"].round().astype("Int64")
    tabela = tabela[COLUNAS]

    # Converte NaN do pandas em NULL do SQL.
    linhas = [
        tuple(None if pd.isna(valor) else valor for valor in linha)
        for linha in tabela.itertuples(index=False)
    ]
    # Tipos do numpy (int64) não são aceitos pelo sqlite3; convertemos para tipos do Python.
    linhas = [tuple(v.item() if hasattr(v, "item") else v for v in linha) for linha in linhas]

    marcadores = ", ".join("?" for _ in COLUNAS)
    atualizacoes = ", ".join(
        f"{coluna} = excluded.{coluna}"
        for coluna in COLUNAS
        if coluna not in ("geocodigo", "ano", "semana")
    )
    comando = (
        f"INSERT INTO semanas ({', '.join(COLUNAS)}) VALUES ({marcadores}) "
        f"ON CONFLICT (geocodigo, ano, semana) DO UPDATE SET {atualizacoes}"
    )

    Path(caminho_banco).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(caminho_banco) as conexao:
        conexao.execute(CRIAR_TABELA)
        conexao.executemany(comando, linhas)
    return len(linhas)


def consultar(caminho_banco: Path, sql: str, parametros: tuple = ()) -> pd.DataFrame:
    """Roda uma consulta SQL e devolve o resultado como DataFrame."""
    with sqlite3.connect(caminho_banco) as conexao:
        return pd.read_sql_query(sql, conexao, params=parametros)
