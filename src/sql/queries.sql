-- ============================================================
-- C2 — Requêtes SQL d'extraction et d'analyse
-- Niveau avancé : CTEs, window functions, sous-requêtes corrélées
-- ============================================================

-- ──────────────────────────────────────────
-- 1) CTE — Avis de haute qualité avec ranking
-- ──────────────────────────────────────────
WITH high_quality AS (
    SELECT
        id,
        review_text,
        sentiment,
        source,
        quality_score,
        ROW_NUMBER() OVER (PARTITION BY sentiment ORDER BY quality_score DESC) AS rank_in_sentiment
    FROM reviews
    WHERE quality_score >= 60
)
SELECT * FROM high_quality
WHERE rank_in_sentiment <= 10
ORDER BY sentiment, rank_in_sentiment;

-- ──────────────────────────────────────────
-- 2) Window function — Moyenne glissante de qualité par bloc de 100 avis
-- ──────────────────────────────────────────
SELECT
    id,
    quality_score,
    AVG(quality_score) OVER (ORDER BY id ROWS BETWEEN 49 PRECEDING AND 50 FOLLOWING) AS rolling_avg_quality,
    sentiment
FROM reviews
ORDER BY id
LIMIT 200;

-- ──────────────────────────────────────────
-- 3) Distribution des sentiments par source avec pourcentages
-- ──────────────────────────────────────────
SELECT
    source,
    sentiment,
    COUNT(*) AS nb,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY source), 1) AS pct_in_source,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_total
FROM reviews
WHERE sentiment IS NOT NULL
GROUP BY source, sentiment
ORDER BY source, sentiment;

-- ──────────────────────────────────────────
-- 4) CTE récursive — Top films par volume avec cumul
-- ──────────────────────────────────────────
WITH film_stats AS (
    SELECT
        f.title,
        f.imdb_rating,
        f.year,
        f.director,
        COUNT(r.id) AS nb_reviews,
        ROUND(AVG(r.quality_score), 1) AS avg_quality,
        SUM(CASE WHEN r.sentiment = 'positive' THEN 1 ELSE 0 END) AS nb_positive,
        SUM(CASE WHEN r.sentiment = 'negative' THEN 1 ELSE 0 END) AS nb_negative
    FROM films f
    INNER JOIN reviews r ON f.id = r.film_id
    GROUP BY f.id
),
ranked AS (
    SELECT *,
        RANK() OVER (ORDER BY nb_reviews DESC) AS rank_volume,
        SUM(nb_reviews) OVER (ORDER BY nb_reviews DESC) AS cumul_reviews,
        ROUND(nb_positive * 100.0 / NULLIF(nb_positive + nb_negative, 0), 1) AS pct_positive
    FROM film_stats
)
SELECT * FROM ranked
ORDER BY rank_volume;

-- ──────────────────────────────────────────
-- 5) Analyse croisée prédiction vs réalité (accuracy par tranche de qualité)
-- ──────────────────────────────────────────
SELECT
    CASE
        WHEN r.quality_score >= 80 THEN 'A (80-100) Excellent'
        WHEN r.quality_score >= 60 THEN 'B (60-79) Bon'
        WHEN r.quality_score >= 40 THEN 'C (40-59) Moyen'
        ELSE 'D (0-39) Faible'
    END AS quality_grade,
    COUNT(*) AS nb_predictions,
    SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) AS correct,
    ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS accuracy_pct,
    ROUND(AVG(p.confidence_score), 3) AS avg_confidence
FROM reviews r
INNER JOIN predictions p ON r.id = p.review_id
WHERE r.sentiment IS NOT NULL
GROUP BY quality_grade
ORDER BY quality_grade;

-- ──────────────────────────────────────────
-- 6) Percentiles de longueur par sentiment
-- ──────────────────────────────────────────
WITH length_ranked AS (
    SELECT
        sentiment,
        text_length,
        NTILE(4) OVER (PARTITION BY sentiment ORDER BY text_length) AS quartile
    FROM reviews
    WHERE sentiment IS NOT NULL AND text_length > 0
)
SELECT
    sentiment,
    quartile,
    MIN(text_length) AS min_len,
    MAX(text_length) AS max_len,
    COUNT(*) AS nb
FROM length_ranked
GROUP BY sentiment, quartile
ORDER BY sentiment, quartile;

-- ──────────────────────────────────────────
-- 7) Corrélation note IMDB ↔ sentiment des avis
-- ──────────────────────────────────────────
SELECT
    f.title,
    f.imdb_rating,
    COUNT(r.id) AS nb_avis,
    ROUND(SUM(CASE WHEN r.sentiment = 'positive' THEN 1.0 ELSE 0 END) / COUNT(r.id) * 100, 1) AS pct_positif_dataset,
    ROUND(SUM(CASE WHEN p.predicted_sentiment = 'positive' THEN 1.0 ELSE 0 END) / NULLIF(COUNT(p.id), 0) * 100, 1) AS pct_positif_ia,
    ROUND(ABS(
        SUM(CASE WHEN r.sentiment = 'positive' THEN 1.0 ELSE 0 END) / COUNT(r.id) -
        SUM(CASE WHEN p.predicted_sentiment = 'positive' THEN 1.0 ELSE 0 END) / NULLIF(COUNT(p.id), 0)
    ) * 100, 1) AS ecart_dataset_vs_ia
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
LEFT JOIN predictions p ON r.id = p.review_id
GROUP BY f.id
HAVING nb_avis >= 5
ORDER BY f.imdb_rating DESC;

-- ──────────────────────────────────────────
-- 8) Data lineage — traçabilité des opérations
-- ──────────────────────────────────────────
SELECT
    operation,
    table_name,
    records_affected,
    details,
    executed_at
FROM data_lineage
ORDER BY executed_at DESC
LIMIT 20;

-- ──────────────────────────────────────────
-- 9) Utilisation de la vue matérialisée v_reviews_enriched
-- ──────────────────────────────────────────
SELECT
    film_title,
    COUNT(*) AS nb_reviews,
    SUM(is_correct) AS correct_predictions,
    ROUND(AVG(confidence_score), 3) AS avg_confidence,
    ROUND(SUM(is_correct) * 100.0 / NULLIF(COUNT(*), 0), 1) AS accuracy_pct
FROM v_reviews_enriched
WHERE predicted_sentiment IS NOT NULL
  AND true_sentiment IS NOT NULL
  AND film_title IS NOT NULL
GROUP BY film_title
ORDER BY nb_reviews DESC;

-- ──────────────────────────────────────────
-- 10) Vue métriques modèle (agrégation depuis la vue)
-- ──────────────────────────────────────────
SELECT * FROM v_model_metrics;
