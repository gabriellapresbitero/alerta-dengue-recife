# 🦟 Alerta Dengue Recife

[![Testes](https://github.com/gabriellapresbitero/alerta-dengue-recife/actions/workflows/testes.yml/badge.svg)](https://github.com/gabriellapresbitero/alerta-dengue-recife/actions/workflows/testes.yml)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

Pipeline de dados que detecta **surtos de dengue** nas cidades da Região Metropolitana do Recife,
semana a semana, usando dados públicos do [InfoDengue](https://info.dengue.mat.br).

## O problema

Todo ano, entre março e julho, os casos de dengue sobem em Pernambuco. A pergunta que a
vigilância em saúde precisa responder toda semana é:

> **"O número de casos desta semana é normal para a época, ou é o começo de uma epidemia?"**

Olhar só o total de casos não basta: 300 casos em abril podem ser normais, e os mesmos 300
casos em outubro podem ser um alerta. Por isso, este projeto compara cada semana com o
que aconteceu **na mesma semana dos anos anteriores**. É a técnica do **canal endêmico**, usada
pelas secretarias de saúde.

## O que o projeto faz

```
InfoDengue (API)  →  limpeza  →  canal endêmico  →  regras de alerta  →  SQLite + CSV + gráfico + relatório
```

1. **Coleta:** baixa a série semanal de casos pela API do InfoDengue e guarda o CSV em cache.
2. **Limpeza:** padroniza as colunas, remove semanas duplicadas ou inválidas e calcula a
   **incidência** (casos por 100 mil habitantes), para comparar cidades de tamanhos diferentes.
3. **Canal endêmico:** para cada semana do ano, calcula o 1º quartil, a mediana e o 3º quartil
   dos anos de referência.
4. **Alertas:** classifica cada semana em um nível e explica o motivo por escrito:

   | Nível | Quando |
   |---|---|
   | 🟢 verde | dentro do esperado para a época |
   | 🟡 amarelo | acima da mediana histórica **ou** casos subindo 20%+ |
   | 🟠 laranja | acima da mediana **e** subindo, ou primeira semana acima do Q3 |
   | 🔴 vermelho | acima do Q3 (zona de epidemia) por 2 semanas seguidas |

5. **Saídas**
   - `dengue.db`: banco **SQLite** com o histórico. Veja as consultas prontas em [`sql/consultas.sql`](sql/consultas.sql).
   - `semanas_para_powerbi.csv`: CSV com `;` e vírgula decimal, que abre direto no Excel e no **Power BI**.
   - `canal_endemico.png`: gráfico com as zonas do canal e a curva do ano.
   - `relatorio.md`: resumo da situação atual e das últimas semanas.

### Decisões e cuidados com os dados

- **Atraso de notificação:** os casos de uma semana continuam chegando por várias semanas.
  Para as semanas recentes, uso a estimativa corrigida do InfoDengue (`casos_est`) em vez do
  número bruto, que sempre parece "cair" no fim da série.
- **Alarme falso:** com poucos casos, uma semana isolada pode passar do limite por acaso.
  Por isso, o vermelho só é emitido se isso se repetir por 2 semanas seguidas.
- **Anos epidêmicos:** se um ano teve epidemia, ele "infla" o canal e esconde surtos futuros.
  A opção `--excluir-anos` tira esses anos da referência.
- **Semana 53:** nem todo ano tem semana 53. Quando ela falta, o canal repete a semana 52.

## Como rodar

Pré-requisito: Python 3.11 ou mais novo.

```bash
git clone https://github.com/gabriellapresbitero/alerta-dengue-recife.git
cd alerta-dengue-recife
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Recife, ano atual, usando os 5 anos anteriores como referência
python -m alerta_dengue --municipio recife

# Olinda em 2025, sem usar 2024 (ano epidêmico) na referência
python -m alerta_dengue --municipio olinda --ano 2025 --excluir-anos 2024
```

Municípios com nome curto: `recife`, `olinda`, `jaboatao`, `paulista` e `camaragibe`.
Para outra cidade, passe o **geocódigo do IBGE** (ex.: `--municipio 2611606`).

Os resultados ficam em `saida/<geocodigo>_<ano>/`.

## Testes

```bash
python -m unittest discover -s tests -t . -v
```

Os testes não usam a internet: geram dados no mesmo formato da API. Eles cobrem a limpeza, o
cálculo dos quartis, as regras de alerta e o pipeline completo, incluindo a gravação no banco
e as consultas SQL. O GitHub Actions roda os testes a cada push, em Python 3.11, 3.12 e 3.13.

## Estrutura

```
alerta_dengue/
├── __main__.py        # linha de comando e orquestração das etapas
├── coleta.py          # API do InfoDengue (com cache e novas tentativas)
├── limpeza.py         # padronização e incidência
├── canal_endemico.py  # quartis por semana e classificação em zonas
├── alertas.py         # regras de nível de alerta e crescimento
├── banco.py           # SQLite (upsert) e consultas
├── relatorio.py       # gráfico e relatório em Markdown
└── municipios.py      # geocódigos da Região Metropolitana do Recife
sql/consultas.sql      # consultas de exemplo
tests/                 # testes com unittest
```

## Próximos passos

- [ ] Rodar toda segunda-feira com GitHub Actions e publicar o relatório
- [ ] Painel no Power BI a partir do CSV
- [ ] Incluir chikungunya e zika (a API já aceita `disease=chikungunya` e `disease=zika`)

## Fonte dos dados

[InfoDengue](https://info.dengue.mat.br), da Fiocruz e da FGV. Os dados são públicos e vêm das
notificações do SINAN.

---
Feito por **Gabriella Presbítero** · Licença MIT
