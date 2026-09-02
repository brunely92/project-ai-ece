"""
C4 — Import base de données avec traçabilité (data lineage)
Gère le nouveau schéma normalisé 3NF.
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path("data/movies_reviews.sqlite")
SCHEMA_PATH = Path("src/sql/schema.sql")
PROCESSED_FILE = Path("data/processed/reviews_clean.csv")


def create_database():
    if not SCHEMA_PATH.exists():
        print(f"[ERREUR] Schéma introuvable : {SCHEMA_PATH}")
        sys.exit(1)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(schema)
    conn.close()
    print(f"[OK] Base créée : {DB_PATH}")


def log_lineage(conn, operation, table, count, details=""):
    conn.execute(
        "INSERT INTO data_lineage (operation, table_name, records_affected, details) VALUES (?, ?, ?, ?)",
        (operation, table, count, details),
    )


def import_reviews(conn):
    if not PROCESSED_FILE.exists():
        print(f"[ERREUR] Dataset introuvable : {PROCESSED_FILE}")
        sys.exit(1)

    df = pd.read_csv(PROCESSED_FILE)
    imported = 0
    rejected = 0

    for _, row in df.iterrows():
        try:
            conn.execute(
                """INSERT INTO reviews (review_text, sentiment, source, quality_score, text_length, word_count, imported_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["review_text"],
                    row.get("sentiment") if pd.notna(row.get("sentiment")) else None,
                    row["source"],
                    int(row.get("quality_score", 0)),
                    int(row.get("text_length", 0)),
                    int(row.get("word_count", 0)),
                    datetime.now().isoformat(),
                ),
            )
            imported += 1
        except Exception:
            rejected += 1

    conn.commit()
    log_lineage(conn, "IMPORT", "reviews", imported, f"imported={imported}, rejected={rejected}")
    conn.commit()
    return {"imported": imported, "rejected": rejected}


def import_sources(conn):
    sources = [
        ("csv_kaggle", "csv", "https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews", "Dataset IMDB Kaggle 50K reviews"),
        ("api_omdb", "api", "https://www.omdbapi.com/", "API OMDB enrichissement films"),
        ("api_tmdb", "api", "https://api.themoviedb.org/3/movie/popular", "API TMDB films populaires"),
        ("scraping_imdb", "scraping", "https://www.imdb.com/title/*/reviews/", "Scraping reviews IMDB"),
        ("sst2_stanford", "api", "https://huggingface.co/datasets/stanfordnlp/sst2", "SST-2 Stanford 67K phrases (Socher et al. 2013)"),
        ("rotten_tomatoes", "api", "https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes", "Rotten Tomatoes Cornell 10K (Pang & Lee 2005)"),
        ("amazon_reviews", "api", "https://huggingface.co/datasets/amazon_polarity", "Amazon Reviews 50K subset (McAuley & Leskovec 2013)"),
        ("yelp_reviews", "api", "https://huggingface.co/datasets/yelp_polarity", "Yelp Reviews 50K subset (Zhang, Zhao & LeCun 2015)"),
    ]
    for name, stype, url, desc in sources:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO sources (name, type, url, description, collected_at) VALUES (?, ?, ?, ?, ?)",
                (name, stype, url, desc, datetime.now().isoformat()),
            )
        except Exception:
            pass
    conn.commit()
    log_lineage(conn, "IMPORT", "sources", len(sources), "sources de collecte enregistrées")
    conn.commit()
    print("[OK] Sources enregistrées")


def verify_import(conn):
    print("\n--- Vérification ---")
    for table in ["sources", "genres", "films", "reviews", "predictions", "data_lineage"]:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:15s} : {count} lignes")
        except Exception:
            pass

    # Stats qualité
    avg_q = conn.execute("SELECT ROUND(AVG(quality_score), 1) FROM reviews WHERE quality_score > 0").fetchone()[0]
    if avg_q:
        print(f"\n  Score qualité moyen : {avg_q}/100")

    by_source = conn.execute("SELECT source, COUNT(*) FROM reviews GROUP BY source ORDER BY COUNT(*) DESC").fetchall()
    print("\n  Par source :")
    for src, count in by_source:
        print(f"    {src:20s} : {count} avis")

    by_sent = conn.execute("SELECT sentiment, COUNT(*) FROM reviews WHERE sentiment IS NOT NULL GROUP BY sentiment").fetchall()
    print("\n  Par sentiment :")
    for sent, count in by_sent:
        print(f"    {sent:20s} : {count} avis")


def main():
    print("=" * 60)
    print(f"IMPORT BASE DE DONNÉES — {datetime.now().isoformat()}")
    print("=" * 60)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print("[INFO] Base existante supprimée")

    create_database()
    conn = sqlite3.connect(DB_PATH)
    import_sources(conn)
    result = import_reviews(conn)
    print(f"\n[OK] Import : {result['imported']} importés, {result['rejected']} rejetés")
    verify_import(conn)
    conn.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
