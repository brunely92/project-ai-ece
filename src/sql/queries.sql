-- ============================================================
-- C2 — Requêtes SQL d'extraction et d'analyse
-- Projet : Analyse de sentiment d'avis de films
-- ============================================================

-- 1) Contrôle volumétrie globale
-- Objectif : vérifier le nombre total d'avis importés
SELECT COUNT(*) AS nb_total_reviews FROM reviews;

-- 2) Extraction des avis exploitables pour le modèle IA
-- Justification filtre : on exclut les avis sans texte ou sans label sentiment
SELECT
    r.id,
    r.review_text,
    r.sentiment,
    r.source,
    f.title AS film_title
FROM reviews r
LEFT JOIN films f ON r.film_id = f.id
WHERE r.review_text IS NOT NULL
  AND r.sentiment IS NOT NULL
  AND LENGTH(r.review_text) > 20;

-- 3) Distribution des sentiments
-- Objectif : vérifier l'équilibre positif/négatif du dataset
SELECT
    sentiment,
    COUNT(*) AS nb_avis,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM reviews), 1) AS pourcentage
FROM reviews
WHERE sentiment IS NOT NULL
GROUP BY sentiment
ORDER BY nb_avis DESC;

-- 4) Nombre d'avis par source de collecte
-- Objectif : prouver la diversité des sources (C1)
SELECT
    source,
    COUNT(*) AS nb_avis
FROM reviews
GROUP BY source
ORDER BY nb_avis DESC;

-- 5) Films les plus commentés (jointure reviews + films)
-- Justification jointure : relier les avis aux métadonnées films
SELECT
    f.title,
    f.vote_average AS note_tmdb,
    COUNT(r.id) AS nb_avis,
    ROUND(AVG(CASE WHEN r.sentiment = 'positive' THEN 1 ELSE 0 END) * 100, 1) AS pct_positif
FROM films f
INNER JOIN reviews r ON f.id = r.film_id
GROUP BY f.id, f.title, f.vote_average
HAVING nb_avis >= 3
ORDER BY nb_avis DESC
LIMIT 20;

-- 6) Avis récents triés par date
-- Objectif : extraire un échantillon temporel
SELECT
    r.id,
    r.review_text,
    r.sentiment,
    r.created_at
FROM reviews r
WHERE r.created_at IS NOT NULL
ORDER BY r.created_at DESC
LIMIT 50;

-- 7) Longueur moyenne des avis par sentiment
-- Objectif : détecter un biais de longueur
SELECT
    sentiment,
    COUNT(*) AS nb,
    ROUND(AVG(LENGTH(review_text)), 0) AS longueur_moyenne,
    MIN(LENGTH(review_text)) AS longueur_min,
    MAX(LENGTH(review_text)) AS longueur_max
FROM reviews
WHERE review_text IS NOT NULL
GROUP BY sentiment;
