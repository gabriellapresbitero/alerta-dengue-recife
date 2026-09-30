"""Coleta dos dados semanais de dengue na API pública do InfoDengue.

Documentação da API: https://info.dengue.mat.br/services/api
"""

from __future__ import annotations

import io
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

URL_API = "https://info.dengue.mat.br/api/alertcity"


def montar_url(geocodigo: int, ano_inicio: int, ano_fim: int, doenca: str = "dengue") -> str:
    """Monta a URL da API pedindo todas as semanas epidemiológicas do período."""
    parametros = {
        "geocode": geocodigo,
        "disease": doenca,
        "format": "csv",
        "ew_start": 1,
        "ew_end": 53,
        "ey_start": ano_inicio,
        "ey_end": ano_fim,
    }
    return f"{URL_API}?{urllib.parse.urlencode(parametros)}"


def baixar_serie(
    geocodigo: int,
    ano_inicio: int,
    ano_fim: int,
    doenca: str = "dengue",
    pasta_cache: Path | None = None,
    tentativas: int = 3,
) -> pd.DataFrame:
    """Baixa a série semanal de casos de um município.

    Se `pasta_cache` for informada, o CSV é salvo em disco. Assim, rodar o
    pipeline de novo não faz outra requisição para a API.
    """
    arquivo_cache = None
    if pasta_cache is not None:
        pasta_cache = Path(pasta_cache)
        pasta_cache.mkdir(parents=True, exist_ok=True)
        arquivo_cache = pasta_cache / f"{doenca}_{geocodigo}_{ano_inicio}_{ano_fim}.csv"
        if arquivo_cache.exists():
            return pd.read_csv(arquivo_cache)

    url = montar_url(geocodigo, ano_inicio, ano_fim, doenca)
    ultimo_erro: Exception | None = None

    for tentativa in range(1, tentativas + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resposta:
                conteudo = resposta.read().decode("utf-8")
            break
        except OSError as erro:  # falha de rede, timeout, erro HTTP
            ultimo_erro = erro
            if tentativa < tentativas:
                time.sleep(2 ** tentativa)  # espera 2s, 4s, ... antes de tentar de novo
    else:
        raise ConnectionError(f"Não foi possível baixar {url}") from ultimo_erro

    tabela = pd.read_csv(io.StringIO(conteudo))
    if tabela.empty:
        raise ValueError("A API não retornou dados para esse município e período.")

    if arquivo_cache is not None:
        tabela.to_csv(arquivo_cache, index=False)
    return tabela
