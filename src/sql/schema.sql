-- ============================================================
-- C4 — Schéma base de données normalisé (3NF)
-- SGBD : SQLite
-- Justification : projet local, sans serveur, intégré Python
--
-- Normalisation :
-- - Table genres séparée (3NF, pas de liste CSV dans une colonne)
-- - Table film_genres (relation N:N films ↔ genres)
-- - Table sources enrichie avec métadonnées de collecte
-- - Index sur colonnes fréquemment recherchées
-- - Vue matérialisée pour les analyses croisées
-- ============================================================

-- Table des genres (normalisée)
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Insertion des genres standards
INSERT OR IGNORE INTO genres (name) VALUES
    ('Action'), ('Adventure'), ('Animation'), ('Comedy'),
    ('Crime'), ('Documentary'), ('Drama'), ('Family'),
    ('Fantasy'), ('History'), ('Horror'), ('Music'),
    ('Mystery'), ('Romance'), ('Sci-Fi'), ('Thriller'),
    ('War'), ('Western'), ('TV Movie');

-- Table des sources de données (traçabilité collecte)
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('csv', 'api', 'scraping', 'manual')),
    url TEXT,
    description TEXT,
    records_count INTEGER DEFAULT 0,
    collected_at TEXT NOT NULL,
    collection_duration_sec REAL,
    errors_count INTEGER DEFAULT 0
);

-- Table des films (métadonnées enrichies)
CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER UNIQUE,
    imdb_id TEXT UNIQUE,
    title TEXT NOT NULL,
    original_title TEXT,
    release_date TEXT,
    year INTEGER,
    runtime INTEGER,
    rated TEXT,
    vote_average REAL,
    vote_count INTEGER,
    popularity REAL,
    genre_ids TEXT,
    overview TEXT,
    original_language TEXT,
    director TEXT,
    actors TEXT,
    awards TEXT,
    metascore INTEGER,
    box_office TEXT,
    imdb_rating REAL,
    imdb_votes INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Relation N:N films ↔ genres
CREATE TABLE IF NOT EXISTS film_genres (
    film_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    PRIMARY KEY (film_id, genre_id),
    FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

-- Table des avis / reviews
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_text TEXT NOT NULL,
    sentiment TEXT CHECK(sentiment IN ('positive', 'negative') OR sentiment IS NULL),
    source TEXT NOT NULL,
    film_id INTEGER,
    author TEXT,
    rating INTEGER CHECK(rating IS NULL OR (rating >= 1 AND rating <= 10)),
    quality_score INTEGER DEFAULT 0,
    text_length INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    created_at TEXT,
    imported_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (film_id) REFERENCES films(id) ON DELETE SET NULL
);

-- Table des prédictions IA
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    predicted_sentiment TEXT NOT NULL CHECK(predicted_sentiment IN ('positive', 'negative')),
    confidence_score REAL NOT NULL CHECK(confidence_score >= 0 AND confidence_score <= 1),
    model_version TEXT NOT NULL,
    processing_time_ms REAL,
    predicted_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);

-- Table d'audit / data lineage
CREATE TABLE IF NOT EXISTS data_lineage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    table_name TEXT NOT NULL,
    records_affected INTEGER,
    details TEXT,
    executed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ══════════════════════════════════════════
-- INDEX pour performance
-- ══════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment);
CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_reviews_film_id ON reviews(film_id);
CREATE INDEX IF NOT EXISTS idx_reviews_quality ON reviews(quality_score);
CREATE INDEX IF NOT EXISTS idx_predictions_review_id ON predictions(review_id);
CREATE INDEX IF NOT EXISTS idx_predictions_sentiment ON predictions(predicted_sentiment);
CREATE INDEX IF NOT EXISTS idx_predictions_confidence ON predictions(confidence_score);
CREATE INDEX IF NOT EXISTS idx_films_title ON films(title);
CREATE INDEX IF NOT EXISTS idx_films_imdb_id ON films(imdb_id);

-- ══════════════════════════════════════════
-- VUES pour analyses croisées
-- ══════════════════════════════════════════

-- Vue : reviews enrichies avec film et prédiction
CREATE VIEW IF NOT EXISTS v_reviews_enriched AS
SELECT
    r.id AS review_id,
    r.review_text,
    r.sentiment AS true_sentiment,
    r.source,
    r.quality_score,
    r.text_length,
    r.word_count,
    f.title AS film_title,
    f.year AS film_year,
    f.genre_ids AS film_genres,
    f.imdb_rating AS film_imdb_rating,
    f.director AS film_director,
    p.predicted_sentiment,
    p.confidence_score,
    p.model_version,
    CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END AS is_correct
FROM reviews r
LEFT JOIN films f ON r.film_id = f.id
LEFT JOIN predictions p ON r.id = p.review_id;

-- Vue : métriques du modèle
CREATE VIEW IF NOT EXISTS v_model_metrics AS
SELECT
    p.model_version,
    COUNT(*) AS total_predictions,
    SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) AS correct,
    ROUND(SUM(CASE WHEN r.sentiment = p.predicted_sentiment THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS accuracy_pct,
    ROUND(AVG(p.confidence_score), 4) AS avg_confidence,
    ROUND(MIN(p.confidence_score), 4) AS min_confidence,
    ROUND(AVG(p.processing_time_ms), 1) AS avg_latency_ms
FROM predictions p
JOIN reviews r ON p.review_id = r.id
WHERE r.sentiment IS NOT NULL
GROUP BY p.model_version;

-- Vue : résumé par film
CREATE VIEW IF NOT EXISTS v_film_summary AS
SELECT
    f.id,
    f.title,
    f.year,
    f.imdb_rating,
    f.genre_ids,
    f.director,
    COUNT(r.id) AS nb_reviews,
    SUM(CASE WHEN r.sentiment = 'positive' THEN 1 ELSE 0 END) AS nb_positive,
    SUM(CASE WHEN r.sentiment = 'negative' THEN 1 ELSE 0 END) AS nb_negative,
    ROUND(AVG(r.quality_score), 1) AS avg_quality,
    ROUND(AVG(r.text_length), 0) AS avg_review_length
FROM films f
LEFT JOIN reviews r ON f.id = r.film_id
GROUP BY f.id;
