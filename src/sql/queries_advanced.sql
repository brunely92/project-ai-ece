-- ============================================================
-- C2 — Requêtes SQL avancées (jointures multi-tables)
-- Après enrichissement : films + reviews + predictions liés
-- ============================================================

-- 1) Sentiment moyen par film (jointure reviews + films + predictions)
-- Objectif : voir quels films sont les mieux perçus par le modèle IA
SELECT
    f.title,
    f.vote_average AS note_tmdb,
    COUNT(p.id) AS nb_predictions,
    ROUND(AVG(p.confidence_score), 3) AS score_confiance_moyen,
    ROUND(SUM(CASE WHEN p.predicted_sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id), 1) AS pct_positif_ia,
    ROUND(SUM(CASE WHEN r.sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(r.id), 1) AS pct_positif_reel
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
INNER JOIN predictions p ON r.id = p.review_id
GROUP BY f.id, f.title, f.vote_average
HAVING nb_predictions >= 3
ORDER BY pct_positif_ia DESC;

-- 2) Comparaison prédiction IA vs label réel (accuracy par film)
SELECT
    f.title,
    COUNT(*) AS nb_avis,
    SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) AS correct,
    ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS accuracy_pct
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
INNER JOIN predictions p ON r.id = p.review_id
WHERE r.sentiment IS NOT NULL
GROUP BY f.id, f.title
HAVING nb_avis >= 3
ORDER BY accuracy_pct ASC;

-- 3) Films par genre avec sentiment agrégé
SELECT
    f.genre_ids AS genre,
    COUNT(DISTINCT f.id) AS nb_films,
    COUNT(r.id) AS nb_avis,
    ROUND(AVG(f.vote_average), 1) AS note_tmdb_moyenne,
    ROUND(SUM(CASE WHEN p.predicted_sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id), 1) AS pct_positif_ia
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
LEFT JOIN predictions p ON r.id = p.review_id
GROUP BY f.genre_ids
ORDER BY nb_avis DESC;

-- 4) Prédictions les moins confiantes (potentielles erreurs)
SELECT
    r.id AS review_id,
    SUBSTR(r.review_text, 1, 80) AS extrait,
    r.sentiment AS vrai_label,
    p.predicted_sentiment AS prediction,
    p.confidence_score,
    CASE WHEN r.sentiment = p.predicted_sentiment THEN 'CORRECT' ELSE 'ERREUR' END AS resultat
FROM reviews r
INNER JOIN predictions p ON r.id = p.review_id
WHERE r.sentiment IS NOT NULL
ORDER BY p.confidence_score ASC
LIMIT 20;

-- 5) Distribution des scores de confiance par tranche
SELECT
    CASE
        WHEN confidence_score >= 0.99 THEN '0.99-1.00 (très confiant)'
        WHEN confidence_score >= 0.95 THEN '0.95-0.99'
        WHEN confidence_score >= 0.90 THEN '0.90-0.95'
        WHEN confidence_score >= 0.80 THEN '0.80-0.90'
        WHEN confidence_score >= 0.60 THEN '0.60-0.80'
        ELSE '0.50-0.60 (incertain)'
    END AS tranche_confiance,
    COUNT(*) AS nb,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM predictions), 1) AS pct
FROM predictions
GROUP BY tranche_confiance
ORDER BY MIN(confidence_score) DESC;

-- 6) Corrélation note TMDB vs sentiment IA
SELECT
    CASE
        WHEN f.vote_average >= 8.0 THEN '8.0+ (excellent)'
        WHEN f.vote_average >= 7.0 THEN '7.0-7.9 (bon)'
        WHEN f.vote_average >= 6.0 THEN '6.0-6.9 (moyen)'
        ELSE '< 6.0 (faible)'
    END AS tranche_note,
    COUNT(p.id) AS nb_avis,
    ROUND(SUM(CASE WHEN p.predicted_sentiment = 'positive' THEN 1 ELSE 0 END) * 100.0 / COUNT(p.id), 1) AS pct_positif
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
INNER JOIN predictions p ON r.id = p.review_id
GROUP BY tranche_note
ORDER BY MIN(f.vote_average) DESC;
