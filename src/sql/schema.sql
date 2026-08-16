-- ============================================================
-- C4 — Schéma de la base de données
-- SGBD : SQLite
-- Justification : projet local, léger, sans serveur
-- ============================================================

-- Table des sources de données
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('csv', 'api', 'scraping', 'manual')),
    url TEXT,
    description TEXT,
    collected_at TEXT NOT NULL
);

-- Table des films (métadonnées TMDB)
CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tmdb_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    original_title TEXT,
    release_date TEXT,
    vote_average REAL,
    vote_count INTEGER,
    popularity REAL,
    genre_ids TEXT,
    overview TEXT,
    original_language TEXT
);

-- Table des avis / reviews
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_text TEXT NOT NULL,
    sentiment TEXT CHECK(sentiment IN ('positive', 'negative', NULL)),
    source TEXT NOT NULL,
    film_id INTEGER,
    author TEXT,
    created_at TEXT,
    imported_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (film_id) REFERENCES films(id)
);

-- Table des prédictions IA
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL,
    predicted_sentiment TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    model_version TEXT NOT NULL,
    predicted_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);
