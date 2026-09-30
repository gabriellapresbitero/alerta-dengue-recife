"""Geração do gráfico do canal endêmico e do relatório em Markdown."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera imagens sem precisar de tela (funciona em servidor e no CI)
import matplotlib.pyplot as plt
import pandas as pd

CORES_ZONAS = {
    "sucesso": "#cfe8cf",
    "seguranca": "#fff3b0",
    "alerta": "#ffd199",
    "epidemia": "#f4a3a3",
}

EMOJI_NIVEL = {"verde": "🟢", "amarelo": "🟡", "laranja": "🟠", "vermelho": "🔴"}


def gerar_grafico(canal: pd.DataFrame, avaliacao: pd.DataFrame, titulo: str, caminho: Path) -> Path:
    """Desenha as quatro zonas do canal endêmico e a curva do ano analisado."""
    semanas = canal.index
    teto = max(canal["q3"].max(), avaliacao["incidencia"].max()) * 1.15 or 1

    figura, eixo = plt.subplots(figsize=(11, 5))
    eixo.fill_between(semanas, 0, canal["q1"], color=CORES_ZONAS["sucesso"], label="Sucesso (< Q1)")
    eixo.fill_between(semanas, canal["q1"], canal["mediana"], color=CORES_ZONAS["seguranca"], label="Segurança")
    eixo.fill_between(semanas, canal["mediana"], canal["q3"], color=CORES_ZONAS["alerta"], label="Alerta")
    eixo.fill_between(semanas, canal["q3"], teto, color=CORES_ZONAS["epidemia"], label="Epidemia (> Q3)")
    eixo.plot(avaliacao["semana"], avaliacao["incidencia"], color="black", linewidth=2, marker="o",
              markersize=3, label="Ano analisado")

    eixo.set_xlim(1, 53)
    eixo.set_ylim(0, teto)
    eixo.set_xlabel("Semana epidemiológica")
    eixo.set_ylabel("Casos por 100 mil habitantes")
    eixo.set_title(titulo)
    eixo.legend(loc="upper right", fontsize=8)
    figura.tight_layout()

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(caminho, dpi=120)
    plt.close(figura)
    return caminho


def gerar_markdown(avaliacao: pd.DataFrame, titulo: str, anos_referencia: list[int],
                   nome_grafico: str, ultimas: int = 8) -> str:
    """Monta um relatório curto com a situação atual e as últimas semanas."""
    atual = avaliacao.iloc[-1]
    recentes = avaliacao.tail(ultimas)

    linhas = [
        f"# {titulo}",
        "",
        f"**Situação na semana {atual.semana}/{atual.ano}:** "
        f"{EMOJI_NIVEL[atual.nivel]} **{atual.nivel.upper()}** ({atual.motivo}).",
        "",
        f"Anos de referência do canal endêmico: {', '.join(map(str, anos_referencia))}.",
        "",
        f"![Canal endêmico]({nome_grafico})",
        "",
        f"## Últimas {len(recentes)} semanas",
        "",
        "| Semana | Início | Casos (estimados) | Incidência /100 mil | Zona | Crescimento | Nível |",
        "|---:|---|---:|---:|---|---:|---|",
    ]
    for linha in recentes.itertuples():
        crescimento = "—" if pd.isna(linha.crescimento) else f"{linha.crescimento:+.0%}"
        linhas.append(
            f"| {linha.semana} | {pd.Timestamp(linha.inicio_semana):%d/%m/%Y} | {linha.casos_estimados} "
            f"| {linha.incidencia:.2f} | {linha.zona} | {crescimento} "
            f"| {EMOJI_NIVEL[linha.nivel]} {linha.nivel} |".replace(".", ",")
        )

    contagem = avaliacao["nivel"].value_counts()
    linhas += [
        "",
        "## Resumo do ano",
        "",
        *[f"- {EMOJI_NIVEL[n]} {n}: {int(contagem.get(n, 0))} semana(s)" for n in EMOJI_NIVEL],
        "",
        "> Os números das últimas semanas são estimativas do InfoDengue que corrigem o "
        "atraso de notificação e podem mudar nas próximas atualizações.",
        "",
    ]
    return "\n".join(linhas)
