"""Ponto de entrada do pipeline.

Uso:
    python -m alerta_dengue --municipio recife --ano 2025

Etapas:
    1. Coleta   -> baixa a série semanal do InfoDengue
    2. Limpeza  -> padroniza colunas e calcula a incidência
    3. Canal    -> monta o canal endêmico com os anos anteriores
    4. Alertas  -> classifica cada semana do ano analisado
    5. Saídas   -> banco SQLite, CSV para Power BI, gráfico e relatório
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import alertas, banco, canal_endemico, coleta, limpeza, relatorio
from .municipios import MUNICIPIOS, resolver_geocodigo


def ler_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="alerta_dengue",
        description="Gera alertas de surto de dengue a partir dos dados do InfoDengue.",
    )
    parser.add_argument("--municipio", default="recife",
                        help=f"Nome ({', '.join(MUNICIPIOS)}) ou geocódigo IBGE. Padrão: recife")
    parser.add_argument("--ano", type=int, default=date.today().year, help="Ano a ser analisado.")
    parser.add_argument("--anos-referencia", type=int, default=5,
                        help="Quantos anos anteriores usar no canal endêmico. Padrão: 5")
    parser.add_argument("--excluir-anos", type=int, nargs="*", default=[],
                        help="Anos epidêmicos a deixar fora da referência (ex.: 2024).")
    parser.add_argument("--saida", type=Path, default=Path("saida"), help="Pasta dos resultados.")
    parser.add_argument("--cache", type=Path, default=Path("dados/brutos"),
                        help="Pasta onde os CSVs baixados ficam guardados.")
    return parser.parse_args(argv)


def executar(args: argparse.Namespace) -> Path:
    geocodigo = resolver_geocodigo(args.municipio)
    nome = args.municipio.title() if not args.municipio.isdigit() else f"município {geocodigo}"

    # Busca anos extras para compensar os anos excluídos.
    primeiro_ano = args.ano - args.anos_referencia - len(args.excluir_anos)
    anos_referencia = [
        ano for ano in range(primeiro_ano, args.ano) if ano not in args.excluir_anos
    ][-args.anos_referencia:]

    print(f"[1/5] Baixando dados de {nome} ({primeiro_ano}–{args.ano})...")
    bruto = coleta.baixar_serie(geocodigo, primeiro_ano, args.ano, pasta_cache=args.cache)

    print("[2/5] Limpando e calculando a incidência...")
    dados = limpeza.padronizar(bruto)

    print(f"[3/5] Montando o canal endêmico com {anos_referencia}...")
    canal = canal_endemico.construir_canal(dados, anos_referencia)

    print(f"[4/5] Avaliando as semanas de {args.ano}...")
    ano_analisado = dados[dados["ano"] == args.ano]
    if ano_analisado.empty:
        raise SystemExit(f"Ainda não há dados de {args.ano} para {nome}.")
    avaliacao = alertas.avaliar_semanas(ano_analisado, canal)

    print("[5/5] Gravando resultados...")
    pasta = args.saida / f"{geocodigo}_{args.ano}"
    pasta.mkdir(parents=True, exist_ok=True)

    banco.salvar(avaliacao, geocodigo, args.saida / "dengue.db")
    avaliacao.assign(geocodigo=geocodigo, municipio=nome).to_csv(
        pasta / "semanas_para_powerbi.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
    )
    canal.to_csv(pasta / "canal_endemico.csv", sep=";", decimal=",", encoding="utf-8-sig")

    titulo = f"Dengue em {nome}: canal endêmico {args.ano}"
    relatorio.gerar_grafico(canal, avaliacao, titulo, pasta / "canal_endemico.png")
    texto = relatorio.gerar_markdown(avaliacao, titulo, anos_referencia, "canal_endemico.png")
    (pasta / "relatorio.md").write_text(texto, encoding="utf-8")

    atual = avaliacao.iloc[-1]
    print(f"\nSemana {atual.semana}/{atual.ano}: nível {atual.nivel.upper()} ({atual.motivo})")
    print(f"Resultados em: {pasta}")
    return pasta


def main(argv: list[str] | None = None) -> int:
    try:
        executar(ler_argumentos(argv))
    except (ValueError, ConnectionError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
