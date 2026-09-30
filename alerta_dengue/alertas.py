"""Regras que transformam os números da semana em um nível de alerta.

A ideia é ser transparente: cada alerta vem com o motivo por escrito,
para que a equipe de saúde saiba exatamente por que ele foi emitido.

Níveis (do mais tranquilo ao mais grave):
    verde    -> situação dentro do esperado
    amarelo  -> atenção: acima da mediana ou crescendo rápido
    laranja  -> acima da mediana E crescendo, ou primeira semana acima do Q3
    vermelho -> zona de epidemia (acima do Q3) por 2 semanas seguidas
"""

from __future__ import annotations

import pandas as pd

from .canal_endemico import classificar_zona

NIVEIS = ["verde", "amarelo", "laranja", "vermelho"]


def calcular_crescimento(casos: pd.Series, janela: int = 3) -> pd.Series:
    """Compara a soma de casos das últimas `janela` semanas com as `janela` anteriores.

    Exemplo com janela=3: se as semanas 8, 9 e 10 somaram 120 casos e as
    semanas 5, 6 e 7 somaram 100, o crescimento é 0,20 (20%).

    Quando o período anterior teve zero casos, o crescimento fica indefinido (NaN).
    """
    atual = casos.rolling(janela).sum()
    anterior = atual.shift(janela)
    crescimento = (atual - anterior) / anterior
    return crescimento.where(anterior > 0)


def avaliar_semanas(
    ano: pd.DataFrame,
    canal: pd.DataFrame,
    limiar_crescimento: float = 0.20,
    janela: int = 3,
) -> pd.DataFrame:
    """Classifica cada semana do ano analisado.

    `ano` deve ser a tabela limpa (saída de `limpeza.padronizar`) filtrada
    para um único ano. Retorna a mesma tabela com as colunas extras:
    q1, mediana, q3, zona, crescimento, nivel, motivo.
    """
    resultado = ano.sort_values("semana").reset_index(drop=True)
    resultado = resultado.join(canal, on="semana")

    resultado["zona"] = [
        classificar_zona(linha.incidencia, linha.q1, linha.mediana, linha.q3)
        for linha in resultado.itertuples()
    ]
    resultado["crescimento"] = calcular_crescimento(resultado["casos_estimados"], janela).round(3)

    niveis, motivos = [], []
    zona_anterior = None
    for linha in resultado.itertuples():
        nivel, motivo = _decidir_nivel(linha.zona, zona_anterior, linha.crescimento, limiar_crescimento)
        niveis.append(nivel)
        motivos.append(motivo)
        zona_anterior = linha.zona
    resultado["nivel"] = niveis
    resultado["motivo"] = motivos
    return resultado


def _decidir_nivel(zona: str, zona_anterior: str | None, crescimento: float,
                   limiar: float) -> tuple[str, str]:
    crescendo = pd.notna(crescimento) and crescimento >= limiar
    texto_crescimento = f"casos subiram {crescimento:.0%} em relação às semanas anteriores"

    # Quando há poucos casos, uma única semana pode passar do Q3 por acaso.
    # Por isso o vermelho só é emitido quando isso se repete por 2 semanas seguidas.
    if zona == "epidemia" and zona_anterior == "epidemia":
        return "vermelho", "incidência acima do quartil superior (Q3) por 2 semanas seguidas"
    if zona == "epidemia":
        return "laranja", "incidência passou do Q3 nesta semana; vira vermelho se continuar"
    if zona == "alerta" and crescendo:
        return "laranja", f"acima da mediana histórica e {texto_crescimento}"
    if zona == "alerta":
        return "amarelo", "incidência acima da mediana histórica"
    if crescendo:
        return "amarelo", f"dentro do esperado, mas {texto_crescimento}"
    return "verde", "dentro do esperado para a época do ano"
