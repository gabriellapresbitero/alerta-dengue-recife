-- Consultas de exemplo para o banco gerado em saida/dengue.db
-- Abra o banco no DB Browser for SQLite, no DBeaver ou pelo terminal:
--     sqlite3 saida/dengue.db < sql/consultas.sql

-- 1) Situação mais recente de cada município
SELECT s.geocodigo, s.ano, s.semana, s.casos_estimados, s.incidencia, s.nivel, s.motivo
FROM semanas AS s
JOIN (
    SELECT geocodigo, MAX(ano * 100 + semana) AS ultima
    FROM semanas
    GROUP BY geocodigo
) AS u
  ON u.geocodigo = s.geocodigo
 AND u.ultima = s.ano * 100 + s.semana;

-- 2) Quantas semanas cada ano passou em cada nível de alerta
SELECT geocodigo, ano, nivel, COUNT(*) AS semanas
FROM semanas
GROUP BY geocodigo, ano, nivel
ORDER BY geocodigo, ano,
         CASE nivel WHEN 'verde' THEN 1 WHEN 'amarelo' THEN 2
                    WHEN 'laranja' THEN 3 ELSE 4 END;

-- 3) Semana de pico de cada ano (maior incidência)
SELECT geocodigo, ano, semana, inicio_semana, incidencia
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY geocodigo, ano ORDER BY incidencia DESC) AS posicao
    FROM semanas
)
WHERE posicao = 1;

-- 4) Primeira semana do ano em que o alerta chegou a laranja ou vermelho
--    (útil para saber com quanta antecedência o sistema avisou)
SELECT geocodigo, ano, MIN(semana) AS primeira_semana_de_alerta
FROM semanas
WHERE nivel IN ('laranja', 'vermelho')
GROUP BY geocodigo, ano;

-- 5) Diferença entre casos notificados e estimados (atraso de notificação)
SELECT geocodigo, ano, semana,
       casos_notificados,
       casos_estimados,
       casos_estimados - casos_notificados AS ainda_nao_notificados
FROM semanas
WHERE casos_estimados > casos_notificados
ORDER BY ano DESC, semana DESC;
